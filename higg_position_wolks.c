// hpwl_engine.h/.cpp (single file is fine) - C++17, no 3rd party libs
#include <cstdint>
#include <vector>
#include <string>
#include <unordered_map>
#include <limits>
#include <stdexcept>

namespace hpwl {

// ===================== INPUT TYPES (fill from your JSON parser) =====================
// Your JSON says: block -> list of variants; variant has nets; nets is map net_name -> list of pins; pin has "__x":[lx,ly]
struct input_pin {
    float local_x = 0.0f;
    float local_y = 0.0f;
};

struct input_net {
    std::string net_name;
    std::vector<input_pin> pins; // pins for this block-variant on this net
};

struct input_variant {
    std::string variant_id;              // "ID" in JSON
    std::vector<input_net> nets;         // converted from JSON dict to a vector
};

struct input_block {
    std::string block_name;              // top-level key
    std::vector<input_variant> variants; // list
};

// ===================== PREPROCESSED DB (built once) =====================
struct pin_packed {
    uint32_t net_id; // 0..N-1
    float dx;        // local_x
    float dy;        // local_y
};

struct variant_span {
    uint32_t pin_begin; // offset into pin_pool
    uint32_t pin_count; // number of pins in that variant
};

struct block_span {
    uint32_t variant_begin; // offset into variant_spans (flat)
    uint32_t variant_count; // number of variants for this block
};

struct preprocessed_db {
    uint32_t num_blocks = 0;
    uint32_t num_nets   = 0;

    // mapping (for debugging / optional external access)
    std::vector<std::string> net_names; // index = net_id
    std::unordered_map<std::string, uint32_t> net_id_of; // only used in preprocessing

    // flat storage
    std::vector<pin_packed>   pin_pool;       // all pins of all variants
    std::vector<variant_span> variant_spans;  // one per (block,variant), flat
    std::vector<block_span>   block_spans;    // one per block

    // ---------- PREPROCESSING ENTRY ----------
    void build_from_parsed(const std::vector<input_block>& blocks) {
        // First pass: count totals and intern nets
        num_blocks = static_cast<uint32_t>(blocks.size());

        uint64_t total_variants = 0;
        uint64_t total_pins     = 0;

        // net_id_of is used only here; reserve to reduce rehashing
        net_id_of.clear();
        net_names.clear();

        // A rough reserve: total net occurrences is <= total_variants * avg_nets.
        // If you can estimate better, do it before calling.
        net_id_of.reserve(16384);

        for (const auto& b : blocks) {
            total_variants += b.variants.size();
            for (const auto& v : b.variants) {
                for (const auto& net : v.nets) {
                    // intern net name -> id
                    auto it = net_id_of.find(net.net_name);
                    if (it == net_id_of.end()) {
                        uint32_t new_id = static_cast<uint32_t>(net_names.size());
                        net_id_of.emplace(net.net_name, new_id);
                        net_names.push_back(net.net_name);
                    }
                    total_pins += net.pins.size();
                }
            }
        }

        num_nets = static_cast<uint32_t>(net_names.size());

        // Allocate flat arrays
        pin_pool.clear();
        variant_spans.clear();
        block_spans.clear();

        pin_pool.reserve(static_cast<size_t>(total_pins));
        variant_spans.reserve(static_cast<size_t>(total_variants));
        block_spans.resize(num_blocks);

        // Second pass: fill spans + pins
        uint32_t variant_cursor = 0;

        for (uint32_t bi = 0; bi < num_blocks; ++bi) {
            const auto& b = blocks[bi];
            const uint32_t vcount = static_cast<uint32_t>(b.variants.size());

            block_spans[bi] = block_span{ variant_cursor, vcount };

            for (uint32_t vi = 0; vi < vcount; ++vi) {
                const auto& v = b.variants[vi];

                const uint32_t pin_begin = static_cast<uint32_t>(pin_pool.size());
                uint32_t pin_count = 0;

                // Flatten pins: (net_id, dx, dy)
                for (const auto& net : v.nets) {
                    const uint32_t nid = net_id_of[net.net_name]; // exists from pass-1
                    for (const auto& p : net.pins) {
                        pin_pool.push_back(pin_packed{ nid, p.local_x, p.local_y });
                        ++pin_count;
                    }
                }

                variant_spans.push_back(variant_span{ pin_begin, pin_count });
                ++variant_cursor;
            }
        }
    }

    // Convenience accessor: span for (block, selected_variant_index)
    inline variant_span get_span(uint32_t block_i, uint32_t variant_i) const {
        const block_span bs = block_spans[block_i];
        if (variant_i >= bs.variant_count) {
            throw std::out_of_range("selected variant index out of range for block");
        }
        return variant_spans[bs.variant_begin + variant_i];
    }
};

// ===================== INITIALIZATION BEFORE OPTIMIZER (once per run) =====================
struct hpwl_runtime {
    // Net extents for CURRENT iteration only (managed by epoch+stamp)
    std::vector<float> minx, maxx, miny, maxy;
    std::vector<uint32_t> stamp;
    std::vector<uint32_t> active_nets;

    uint32_t epoch = 1;

    void init_for_db(const preprocessed_db& db) {
        const uint32_t N = db.num_nets;

        minx.resize(N);
        maxx.resize(N);
        miny.resize(N);
        maxy.resize(N);
        stamp.assign(N, 0);

        active_nets.clear();
        active_nets.reserve(N); // worst-case: all nets touched in an iteration

        epoch = 1;
    }
};

// ===================== HOT PATH (called every optimizer iteration) =====================
// Inputs per iteration:
// - selected_variant[block] : which variant is active for that block
// - block_cx[block], block_cy[block] : current block center positions
//
// Returns: exact HPWL (float)
inline float compute_hpwl(
    const preprocessed_db& db,
    hpwl_runtime& rt,
    const uint32_t* selected_variant,
    const float* block_cx,
    const float* block_cy
) {
    // epoch rollover handling (very rare)
    ++rt.epoch;
    if (rt.epoch == 0) {
        // reset stamps to 0 and restart epoch at 1
        std::fill(rt.stamp.begin(), rt.stamp.end(), 0u);
        rt.epoch = 1;
    }

    rt.active_nets.clear();

    float* minx = rt.minx.data();
    float* maxx = rt.maxx.data();
    float* miny = rt.miny.data();
    float* maxy = rt.maxy.data();
    uint32_t* stamp = rt.stamp.data();

    const uint32_t B = db.num_blocks;
    const pin_packed* pin_pool = db.pin_pool.data();

    // 1) Build per-net extents from selected variant pins
    for (uint32_t bi = 0; bi < B; ++bi) {
        const float cx = block_cx[bi];
        const float cy = block_cy[bi];

        const uint32_t vi = selected_variant[bi];
        const variant_span sp = db.get_span(bi, vi);

        const pin_packed* p = pin_pool + sp.pin_begin;
        const pin_packed* p_end = p + sp.pin_count;

        for (; p != p_end; ++p) {
            const uint32_t n = p->net_id;
            const float gx = cx + p->dx;
            const float gy = cy + p->dy;

            if (stamp[n] != rt.epoch) {
                stamp[n] = rt.epoch;
                minx[n] = gx; maxx[n] = gx;
                miny[n] = gy; maxy[n] = gy;
                rt.active_nets.push_back(n);
            } else {
                // Manual min/max is typically faster than std::min/max
                if (gx < minx[n]) minx[n] = gx;
                if (gx > maxx[n]) maxx[n] = gx;
                if (gy < miny[n]) miny[n] = gy;
                if (gy > maxy[n]) maxy[n] = gy;
            }
        }
    }

    // 2) Sum HPWL only over active nets
    float hpwl_sum = 0.0f;
    const uint32_t* an = rt.active_nets.data();
    const uint32_t* an_end = an + rt.active_nets.size();

    for (; an != an_end; ++an) {
        const uint32_t n = *an;
        hpwl_sum += (maxx[n] - minx[n]) + (maxy[n] - miny[n]);
    }

    return hpwl_sum;
}

} // namespace hpwl