// hpwl_fast.h  (C++17, header-only)
// No JSON parsing. You fill parsed_jblock from your own parser.

#pragma once
#include <cstdint>
#include <vector>
#include <string>
#include <unordered_map>
#include <limits>
#include <algorithm>

namespace hpwl_fast {

// -----------------------------
// Input adapter types (you fill these from your JSON parser)
// -----------------------------

struct parsed_pin {
    float local_x = 0.0f; // from "__x"[0]
    float local_y = 0.0f; // from "__x"[1]
};

struct parsed_variant {
    std::string variant_id; // from "ID" (optional for hpwl)
    // net_name -> list of pins for that net in this variant
    std::unordered_map<std::string, std::vector<parsed_pin>> nets;
};

struct parsed_block {
    std::string block_name;                 // top-level key (optional for hpwl)
    std::vector<parsed_variant> variants;   // list of variant dicts
};

// Top-level: list of blocks (order defines block indices [0..B-1])
using parsed_jblock = std::vector<parsed_block>;


// -----------------------------
// Preprocessed immutable database (Stage 1 output)
// -----------------------------

struct net_local_extents {
    uint32_t net_id = 0;
    float lx_min = 0.0f;
    float lx_max = 0.0f;
    float ly_min = 0.0f;
    float ly_max = 0.0f;
};
static_assert(sizeof(net_local_extents) == 20, "net_local_extents must stay tightly packed (20 bytes).");

struct variant_info {
    uint32_t extents_start = 0;
    uint16_t extents_count = 0;
    uint16_t _pad = 0;
};
static_assert(sizeof(variant_info) == 8, "variant_info expected to be 8 bytes.");

struct hpwl_preprocessed_db {
    uint32_t num_blocks = 0;
    uint32_t num_nets = 0;

    // block_variant_base[b] gives start index into variant_infos for block b
    // block_variant_base has size num_blocks+1, so variant_infos for block b are:
    //   variant_infos[ block_variant_base[b] ... block_variant_base[b+1]-1 ]
    std::vector<uint32_t> block_variant_base;

    // One per (block, variant)
    std::vector<variant_info> variant_infos;

    // Big contiguous array of net-local extents records (one per (block,variant,net))
    std::vector<net_local_extents> extents;

    // Optional (debug): net names indexed by net_id. Can be left empty to save memory.
    std::vector<std::string> net_names;
};


// -----------------------------
// Runtime context (Stage 2 output, shared with Stage 3)
// -----------------------------

struct hpwl_runtime_context {
    uint32_t current_epoch = 1;

    std::vector<uint32_t> epoch; // size = num_nets
    std::vector<float> min_x;    // size = num_nets
    std::vector<float> max_x;    // size = num_nets
    std::vector<float> min_y;    // size = num_nets
    std::vector<float> max_y;    // size = num_nets

    std::vector<uint32_t> visited_net_ids; // nets touched this iteration (deduped via epoch)
};


// -----------------------------
// Stage 1: Preprocessing (offline)
// -----------------------------

inline hpwl_preprocessed_db hpwl_preprocess(const parsed_jblock& in, bool keep_net_names = false) {
    hpwl_preprocessed_db db;
    db.num_blocks = static_cast<uint32_t>(in.size());
    db.block_variant_base.resize(db.num_blocks + 1, 0);

    // Reserve estimates to reduce rehash/realloc overhead in preprocessing.
    uint64_t total_variants = 0;
    uint64_t total_extents_records = 0;

    for (const auto& blk : in) {
        total_variants += blk.variants.size();
        for (const auto& var : blk.variants) {
            total_extents_records += var.nets.size(); // one record per net per variant
        }
    }

    db.variant_infos.reserve(static_cast<size_t>(total_variants));
    db.extents.reserve(static_cast<size_t>(total_extents_records));

    std::unordered_map<std::string, uint32_t> net_name_to_id;
    net_name_to_id.reserve(static_cast<size_t>(std::min<uint64_t>(total_extents_records, 1'000'000ULL)));

    uint32_t running_variant_base = 0;
    db.block_variant_base[0] = 0;

    for (uint32_t b = 0; b < db.num_blocks; ++b) {
        const auto& blk = in[b];
        const uint32_t variant_count = static_cast<uint32_t>(blk.variants.size());

        for (uint32_t v = 0; v < variant_count; ++v) {
            const auto& var = blk.variants[v];

            variant_info vi;
            vi.extents_start = static_cast<uint32_t>(db.extents.size());
            vi.extents_count = 0;

            for (const auto& kv : var.nets) {
                const std::string& net_name = kv.first;
                const auto& pins = kv.second;

                // Map net_name -> net_id
                auto it = net_name_to_id.find(net_name);
                uint32_t net_id;
                if (it == net_name_to_id.end()) {
                    net_id = static_cast<uint32_t>(net_name_to_id.size());
                    net_name_to_id.emplace(net_name, net_id);
                    if (keep_net_names) {
                        if (db.net_names.size() <= net_id) db.net_names.resize(net_id + 1);
                        db.net_names[net_id] = net_name;
                    }
                } else {
                    net_id = it->second;
                }

                // Compute local bounding box for this (block,variant,net) from its pins.
                // Exact: no approximation. Hot path will only use these extremes.
                float lx_min = std::numeric_limits<float>::infinity();
                float lx_max = -std::numeric_limits<float>::infinity();
                float ly_min = std::numeric_limits<float>::infinity();
                float ly_max = -std::numeric_limits<float>::infinity();

                for (const auto& p : pins) {
                    lx_min = std::min(lx_min, p.local_x);
                    lx_max = std::max(lx_max, p.local_x);
                    ly_min = std::min(ly_min, p.local_y);
                    ly_max = std::max(ly_max, p.local_y);
                }

                // If a net exists but has 0 pins, skip it (no contribution).
                if (pins.empty()) {
                    continue;
                }

                db.extents.push_back(net_local_extents{net_id, lx_min, lx_max, ly_min, ly_max});
                ++vi.extents_count;
            }

            db.variant_infos.push_back(vi);
        }

        running_variant_base += variant_count;
        db.block_variant_base[b + 1] = running_variant_base;
    }

    db.num_nets = static_cast<uint32_t>(net_name_to_id.size());
    if (keep_net_names && db.net_names.size() < db.num_nets) {
        db.net_names.resize(db.num_nets);
    }
    return db;
}


// -----------------------------
// Stage 2: Initialization (once before optimizer start)
// -----------------------------

inline hpwl_runtime_context hpwl_init_runtime(const hpwl_preprocessed_db& db) {
    hpwl_runtime_context ctx;
    ctx.current_epoch = 1;

    ctx.epoch.assign(db.num_nets, 0u);
    ctx.min_x.resize(db.num_nets);
    ctx.max_x.resize(db.num_nets);
    ctx.min_y.resize(db.num_nets);
    ctx.max_y.resize(db.num_nets);

    ctx.visited_net_ids.clear();
    ctx.visited_net_ids.reserve(db.num_nets); // ensure no reallocations in hot path

    return ctx;
}


// -----------------------------
// Stage 3: Hot path (optimizer callback)
// -----------------------------
// Inputs:
//  - block_cx, block_cy: arrays of size db.num_blocks
//  - selected_variant_idx: array of size db.num_blocks (0..variants_of_block-1)
// Output: exact HPWL scalar

inline float hpwl_compute_hot(
    const hpwl_preprocessed_db& db,
    hpwl_runtime_context& ctx,
    const float* block_cx,
    const float* block_cy,
    const uint16_t* selected_variant_idx
) {
    ctx.visited_net_ids.clear();

    const uint32_t epoch_now = ctx.current_epoch;

    uint32_t b = 0;
    for (; b < db.num_blocks; ++b) {
        const uint32_t base = db.block_variant_base[b];
        const uint32_t base_next = db.block_variant_base[b + 1];
        const uint32_t variant_count = base_next - base;

        uint32_t v = static_cast<uint32_t>(selected_variant_idx[b]);
        // Assume caller provides valid variant indices for speed.
        // If you need safety in debug builds, you can clamp or assert here.
        if (v >= variant_count) {
            // Skip invalid selection (or clamp). Skipping keeps function total-time predictable.
            continue;
        }

        const variant_info& vi = db.variant_infos[base + v];
        const uint32_t start = vi.extents_start;
        const uint32_t count = static_cast<uint32_t>(vi.extents_count);
        const uint32_t end = start + count;

        const float bx = block_cx[b];
        const float by = block_cy[b];

        for (uint32_t i = start; i < end; ++i) {
            const net_local_extents& e = db.extents[i];
            const uint32_t net = e.net_id;

            const float gx_min = bx + e.lx_min;
            const float gx_max = bx + e.lx_max;
            const float gy_min = by + e.ly_min;
            const float gy_max = by + e.ly_max;

            uint32_t& net_epoch = ctx.epoch[net];
            if (net_epoch != epoch_now) {
                net_epoch = epoch_now;
                ctx.min_x[net] = gx_min;
                ctx.max_x[net] = gx_max;
                ctx.min_y[net] = gy_min;
                ctx.max_y[net] = gy_max;
                ctx.visited_net_ids.push_back(net);
            } else {
                float& mnx = ctx.min_x[net];
                float& mxx = ctx.max_x[net];
                float& mny = ctx.min_y[net];
                float& mxy = ctx.max_y[net];

                if (gx_min < mnx) mnx = gx_min;
                if (gx_max > mxx) mxx = gx_max;
                if (gy_min < mny) mny = gy_min;
                if (gy_max > mxy) mxy = gy_max;
            }
        }
    }

    float hpwl = 0.0f;
    for (uint32_t idx = 0; idx < static_cast<uint32_t>(ctx.visited_net_ids.size()); ++idx) {
        const uint32_t net = ctx.visited_net_ids[idx];
        hpwl += (ctx.max_x[net] - ctx.min_x[net]) + (ctx.max_y[net] - ctx.min_y[net]);
    }

    // Advance epoch; handle wraparound (extremely rare).
    ctx.current_epoch = epoch_now + 1;
    if (ctx.current_epoch == 0) {
        std::fill(ctx.epoch.begin(), ctx.epoch.end(), 0u);
        ctx.current_epoch = 1;
    }

    return hpwl;
}


// -----------------------------
// Example usage (calls are segregated)
// -----------------------------
/*
hpwl_fast::parsed_jblock pj = ...; // filled from your JSON parser

// Stage 1 (offline / separate step):
hpwl_fast::hpwl_preprocessed_db db = hpwl_fast::hpwl_preprocess(pj, false);

// Stage 2 (before optimizer start):
hpwl_fast::hpwl_runtime_context ctx = hpwl_fast::hpwl_init_runtime(db);

// Stage 3 (inside optimizer callback, each iteration):
float hpwl = hpwl_fast::hpwl_compute_hot(db, ctx, block_cx, block_cy, selected_variant_idx);
*/

} // namespace hpwl_fast