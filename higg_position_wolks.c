#pragma once
#include <cstdint>
#include <cstring>
#include <string>
#include <string_view>
#include <vector>
#include <unordered_map>
#include <limits>
#include <cmath>
#include <stdexcept>

class hpwl_preprocessor final {
public:
    // The user walks their already-parsed JSON and calls these callbacks.
    // This keeps preprocessing independent from any JSON library and satisfies "no JSON parsing here".
    struct json_walk_visitor {
        virtual ~json_walk_visitor() = default;

        virtual void begin_block(std::string_view block_name) = 0;
        virtual void begin_variant(uint32_t variant_idx_in_block, std::string_view variant_id) = 0;

        virtual void begin_net(std::string_view net_name) = 0;
        virtual void pin(float local_x, float local_y) = 0;
        virtual void end_net() = 0;

        virtual void end_variant() = 0;
        virtual void end_block() = 0;
    };

    // -------------------- Stage A: Preprocessing (offline) --------------------
    // visit_fn(visitor) must traverse the JSON and invoke the visitor callbacks.
    // Returns an opaque packed blob. Runtime stage does NOT depend on any preprocessing types.
    template <class visit_fn_t>
    static std::vector<uint8_t> preprocess_to_blob(visit_fn_t&& visit_fn, int32_t fixed_scale = 10000) {
        if (fixed_scale <= 0) {
            throw std::runtime_error("hpwl_preprocessor: fixed_scale must be > 0");
        }

        struct builder final : json_walk_visitor {
            int32_t scale = 10000;

            // Global net id mapping (preprocess only).
            std::unordered_map<std::string, uint32_t> net_to_id;

            // Flattened layout.
            std::vector<uint32_t> block_variant_base;
            std::vector<uint16_t> block_variant_count;

            std::vector<uint32_t> variant_contrib_offset;
            std::vector<uint16_t> variant_contrib_count;

            // SoA for contributions
            std::vector<uint32_t> contrib_net_id;
            std::vector<int32_t>  contrib_lminx_q;
            std::vector<int32_t>  contrib_lmaxx_q;
            std::vector<int32_t>  contrib_lminy_q;
            std::vector<int32_t>  contrib_lmaxy_q;

            // Current traversal state
            uint32_t current_block_first_variant = 0;
            uint32_t current_block_variant_count = 0;

            uint32_t current_variant_contrib_start = 0;

            std::string current_net_name;
            bool net_has_pin = false;
            int32_t net_lminx_q = 0, net_lmaxx_q = 0, net_lminy_q = 0, net_lmaxy_q = 0;

            static inline int32_t float_to_q(float v, int32_t scale) {
                // Fast, deterministic rounding to nearest int (ties depend on FP mode; acceptable here).
                // If you need strict banker/away-from-zero rounding, change this.
                float x = v * static_cast<float>(scale);
                return static_cast<int32_t>(x >= 0.0f ? (x + 0.5f) : (x - 0.5f));
            }

            uint32_t get_or_add_net_id(std::string_view net_name) {
                auto it = net_to_id.find(std::string(net_name));
                if (it != net_to_id.end()) return it->second;
                uint32_t nid = static_cast<uint32_t>(net_to_id.size());
                net_to_id.emplace(std::string(net_name), nid);
                return nid;
            }

            void begin_block(std::string_view /*block_name*/) override {
                current_block_first_variant = static_cast<uint32_t>(variant_contrib_offset.size());
                current_block_variant_count = 0;
            }

            void begin_variant(uint32_t /*variant_idx_in_block*/, std::string_view /*variant_id*/) override {
                current_variant_contrib_start = static_cast<uint32_t>(contrib_net_id.size());
                variant_contrib_offset.push_back(current_variant_contrib_start);
                variant_contrib_count.push_back(0); // patch at end_variant
                current_block_variant_count++;
            }

            void begin_net(std::string_view net_name) override {
                current_net_name.assign(net_name.data(), net_name.size());
                net_has_pin = false;

                net_lminx_q = std::numeric_limits<int32_t>::max();
                net_lmaxx_q = std::numeric_limits<int32_t>::min();
                net_lminy_q = std::numeric_limits<int32_t>::max();
                net_lmaxy_q = std::numeric_limits<int32_t>::min();
            }

            void pin(float local_x, float local_y) override {
                int32_t xq = float_to_q(local_x, scale);
                int32_t yq = float_to_q(local_y, scale);
                net_has_pin = true;

                if (xq < net_lminx_q) net_lminx_q = xq;
                if (xq > net_lmaxx_q) net_lmaxx_q = xq;
                if (yq < net_lminy_q) net_lminy_q = yq;
                if (yq > net_lmaxy_q) net_lmaxy_q = yq;
            }

            void end_net() override {
                if (!net_has_pin) return;

                uint32_t nid = get_or_add_net_id(current_net_name);

                contrib_net_id.push_back(nid);
                contrib_lminx_q.push_back(net_lminx_q);
                contrib_lmaxx_q.push_back(net_lmaxx_q);
                contrib_lminy_q.push_back(net_lminy_q);
                contrib_lmaxy_q.push_back(net_lmaxy_q);
            }

            void end_variant() override {
                uint32_t end = static_cast<uint32_t>(contrib_net_id.size());
                uint32_t cnt = end - current_variant_contrib_start;
                variant_contrib_count.back() = static_cast<uint16_t>(cnt);
            }

            void end_block() override {
                block_variant_base.push_back(current_block_first_variant);
                block_variant_count.push_back(static_cast<uint16_t>(current_block_variant_count));
            }
        };

        builder b;
        b.scale = fixed_scale;
        b.net_to_id.reserve(1 << 16); // reduce rehashing for large netlists

        visit_fn(b);

        const uint32_t num_blocks  = static_cast<uint32_t>(b.block_variant_base.size());
        const uint32_t num_variants_total = static_cast<uint32_t>(b.variant_contrib_offset.size());
        const uint32_t num_nets    = static_cast<uint32_t>(b.net_to_id.size());
        const uint32_t num_contrib = static_cast<uint32_t>(b.contrib_net_id.size());

        // ---------------- blob packing (opaque contract) ----------------
        auto align4 = [](std::vector<uint8_t>& out) {
            while (out.size() & 3u) out.push_back(uint8_t{0});
        };

        auto push_u32 = [](std::vector<uint8_t>& out, uint32_t v) {
            uint8_t buf[4];
            std::memcpy(buf, &v, 4);
            out.insert(out.end(), buf, buf + 4);
        };
        auto push_i32 = [](std::vector<uint8_t>& out, int32_t v) {
            uint8_t buf[4];
            std::memcpy(buf, &v, 4);
            out.insert(out.end(), buf, buf + 4);
        };
        auto push_u16 = [](std::vector<uint8_t>& out, uint16_t v) {
            uint8_t buf[2];
            std::memcpy(buf, &v, 2);
            out.insert(out.end(), buf, buf + 2);
        };

        std::vector<uint8_t> blob;
        blob.reserve(
            64
            + num_blocks * (4 + 2)
            + num_variants_total * (4 + 2)
            + num_contrib * (4 + 4 * 4)
        );

        // Header
        // magic 'H','P','W','L'
        push_u32(blob, 0x4C575048u);
        push_u32(blob, 1u);                  // version
        push_i32(blob, b.scale);             // fixed_scale
        push_u32(blob, num_blocks);
        push_u32(blob, num_nets);
        push_u32(blob, num_variants_total);
        push_u32(blob, num_contrib);

        // block_variant_base (u32), block_variant_count (u16)
        align4(blob);
        for (uint32_t i = 0; i < num_blocks; ++i) push_u32(blob, b.block_variant_base[i]);
        align4(blob);
        for (uint32_t i = 0; i < num_blocks; ++i) push_u16(blob, b.block_variant_count[i]);

        // variant_contrib_offset (u32), variant_contrib_count (u16)
        align4(blob);
        for (uint32_t i = 0; i < num_variants_total; ++i) push_u32(blob, b.variant_contrib_offset[i]);
        align4(blob);
        for (uint32_t i = 0; i < num_variants_total; ++i) push_u16(blob, b.variant_contrib_count[i]);

        // contrib arrays (SoA)
        align4(blob);
        for (uint32_t i = 0; i < num_contrib; ++i) push_u32(blob, b.contrib_net_id[i]);

        align4(blob);
        for (uint32_t i = 0; i < num_contrib; ++i) push_i32(blob, b.contrib_lminx_q[i]);
        align4(blob);
        for (uint32_t i = 0; i < num_contrib; ++i) push_i32(blob, b.contrib_lmaxx_q[i]);
        align4(blob);
        for (uint32_t i = 0; i < num_contrib; ++i) push_i32(blob, b.contrib_lminy_q[i]);
        align4(blob);
        for (uint32_t i = 0; i < num_contrib; ++i) push_i32(blob, b.contrib_lmaxy_q[i]);

        align4(blob);
        return blob;
    }
};


class hpwl_engine final {
public:
    // -------------------- Stage B: Initialization (before optimizer) --------------------
    // Prefer moving the blob to avoid copies.
    bool init_from_blob(std::vector<uint8_t> blob) {
        blob_ = std::move(blob);
        return parse_blob_and_init_();
    }

    // Convenience overload (copies)
    bool init_from_blob(const std::vector<uint8_t>& blob) {
        blob_ = blob;
        return parse_blob_and_init_();
    }

    uint32_t block_count() const { return num_blocks_; }
    uint32_t net_count()   const { return num_nets_; }
    int32_t  fixed_scale() const { return fixed_scale_; }

    // Call this from the optimizer callback (public wrapper).
    // selected_variant_idx[b] must be in [0, block_variant_count[b]).
    float compute_hpwl(const float* center_x,
                       const float* center_y,
                       const uint16_t* selected_variant_idx) {
        return hot_path_compute_hpwl_(center_x, center_y, selected_variant_idx);
    }

private:
    // -------------------- Stage C: Hot path (private) --------------------
    float hot_path_compute_hpwl_(const float* center_x,
                                 const float* center_y,
                                 const uint16_t* selected_variant_idx) {
        // epoch-stamp trick to avoid clearing arrays
        ++epoch_;
        if (epoch_ == 0u) { // wrap
            std::fill(stamp_.begin(), stamp_.end(), 0u);
            epoch_ = 1u;
        }

        uint32_t touched_count = 0;

        for (uint32_t b = 0; b < num_blocks_; ++b) {
            const uint32_t base = block_variant_base_[b];
            const uint32_t vg   = base + static_cast<uint32_t>(selected_variant_idx[b]);

            // Quantize centers to fixed-point once per block
            const int32_t cx_q = float_to_q_(center_x[b]);
            const int32_t cy_q = float_to_q_(center_y[b]);

            const uint32_t off = variant_contrib_offset_[vg];
            const uint32_t cnt = static_cast<uint32_t>(variant_contrib_count_[vg]);

            for (uint32_t i = 0; i < cnt; ++i) {
                const uint32_t idx = off + i;
                const uint32_t nid = contrib_net_id_[idx];

                const int32_t gx_minx = cx_q + contrib_lminx_q_[idx];
                const int32_t gx_maxx = cx_q + contrib_lmaxx_q_[idx];
                const int32_t gy_miny = cy_q + contrib_lminy_q_[idx];
                const int32_t gy_maxy = cy_q + contrib_lmaxy_q_[idx];

                if (stamp_[nid] != epoch_) {
                    stamp_[nid] = epoch_;
                    min_x_q_[nid] = gx_minx;
                    max_x_q_[nid] = gx_maxx;
                    min_y_q_[nid] = gy_miny;
                    max_y_q_[nid] = gy_maxy;
                    touched_nets_[touched_count++] = nid;
                } else {
                    // branchless-ish min/max with ternary (typically compiles well)
                    int32_t v;
                    v = min_x_q_[nid]; min_x_q_[nid] = (gx_minx < v) ? gx_minx : v;
                    v = max_x_q_[nid]; max_x_q_[nid] = (gx_maxx > v) ? gx_maxx : v;
                    v = min_y_q_[nid]; min_y_q_[nid] = (gy_miny < v) ? gy_miny : v;
                    v = max_y_q_[nid]; max_y_q_[nid] = (gy_maxy > v) ? gy_maxy : v;
                }
            }
        }

        int64_t hpwl_q = 0;
        for (uint32_t i = 0; i < touched_count; ++i) {
            const uint32_t nid = touched_nets_[i];
            const int32_t dx = max_x_q_[nid] - min_x_q_[nid];
            const int32_t dy = max_y_q_[nid] - min_y_q_[nid];
            hpwl_q += static_cast<int64_t>(dx) + static_cast<int64_t>(dy);
        }

        return static_cast<float>(hpwl_q) * inv_scale_;
    }

private:
    // ---- blob parsing + runtime buffers ----
    static inline uintptr_t align4_ptr_(uintptr_t p) { return (p + 3u) & ~uintptr_t(3u); }

    bool parse_blob_and_init_() {
        if (blob_.size() < 28) return false;

        const uint8_t* data = blob_.data();
        uintptr_t p = reinterpret_cast<uintptr_t>(data);

        auto read_u32 = [&](uint32_t& out) {
            std::memcpy(&out, reinterpret_cast<const void*>(p), 4);
            p += 4;
        };
        auto read_i32 = [&](int32_t& out) {
            std::memcpy(&out, reinterpret_cast<const void*>(p), 4);
            p += 4;
        };

        uint32_t magic = 0, version = 0, nb = 0, nn = 0, nv = 0, nc = 0;
        read_u32(magic);
        read_u32(version);
        read_i32(fixed_scale_);
        read_u32(nb);
        read_u32(nn);
        read_u32(nv);
        read_u32(nc);

        if (magic != 0x4C575048u) return false; // 'HPWL'
        if (version != 1u) return false;
        if (fixed_scale_ <= 0) return false;

        num_blocks_ = nb;
        num_nets_   = nn;
        num_variants_total_ = nv;
        num_contrib_ = nc;

        inv_scale_ = 1.0f / static_cast<float>(fixed_scale_);

        // block_variant_base (u32)
        p = align4_ptr_(p);
        block_variant_base_ = reinterpret_cast<const uint32_t*>(p);
        p += sizeof(uint32_t) * num_blocks_;

        // block_variant_count (u16)
        p = align4_ptr_(p);
        block_variant_count_ = reinterpret_cast<const uint16_t*>(p);
        p += sizeof(uint16_t) * num_blocks_;

        // variant_contrib_offset (u32)
        p = align4_ptr_(p);
        variant_contrib_offset_ = reinterpret_cast<const uint32_t*>(p);
        p += sizeof(uint32_t) * num_variants_total_;

        // variant_contrib_count (u16)
        p = align4_ptr_(p);
        variant_contrib_count_ = reinterpret_cast<const uint16_t*>(p);
        p += sizeof(uint16_t) * num_variants_total_;

        // contrib_net_id (u32)
        p = align4_ptr_(p);
        contrib_net_id_ = reinterpret_cast<const uint32_t*>(p);
        p += sizeof(uint32_t) * num_contrib_;

        // contrib_lminx_q (i32)
        p = align4_ptr_(p);
        contrib_lminx_q_ = reinterpret_cast<const int32_t*>(p);
        p += sizeof(int32_t) * num_contrib_;

        // contrib_lmaxx_q (i32)
        p = align4_ptr_(p);
        contrib_lmaxx_q_ = reinterpret_cast<const int32_t*>(p);
        p += sizeof(int32_t) * num_contrib_;

        // contrib_lminy_q (i32)
        p = align4_ptr_(p);
        contrib_lminy_q_ = reinterpret_cast<const int32_t*>(p);
        p += sizeof(int32_t) * num_contrib_;

        // contrib_lmaxy_q (i32)
        p = align4_ptr_(p);
        contrib_lmaxy_q_ = reinterpret_cast<const int32_t*>(p);
        p += sizeof(int32_t) * num_contrib_;

        // Basic bounds sanity (optional but cheap)
        if (reinterpret_cast<const uint8_t*>(p) > blob_.data() + blob_.size()) return false;

        // Allocate runtime working buffers (shared with hot path)
        stamp_.assign(num_nets_, 0u);
        min_x_q_.resize(num_nets_);
        max_x_q_.resize(num_nets_);
        min_y_q_.resize(num_nets_);
        max_y_q_.resize(num_nets_);
        touched_nets_.resize(num_nets_);
        epoch_ = 1u;

        return true;
    }

    inline int32_t float_to_q_(float v) const {
        float x = v * static_cast<float>(fixed_scale_);
        return static_cast<int32_t>(x >= 0.0f ? (x + 0.5f) : (x - 0.5f));
    }

private:
    // Owned blob (the only shared contract with preprocessing)
    std::vector<uint8_t> blob_;

    // Parsed views into blob
    int32_t fixed_scale_ = 10000;
    float   inv_scale_ = 1.0f / 10000.0f;

    uint32_t num_blocks_ = 0;
    uint32_t num_nets_ = 0;
    uint32_t num_variants_total_ = 0;
    uint32_t num_contrib_ = 0;

    const uint32_t* block_variant_base_ = nullptr;
    const uint16_t* block_variant_count_ = nullptr;

    const uint32_t* variant_contrib_offset_ = nullptr;
    const uint16_t* variant_contrib_count_ = nullptr;

    const uint32_t* contrib_net_id_ = nullptr;
    const int32_t*  contrib_lminx_q_ = nullptr;
    const int32_t*  contrib_lmaxx_q_ = nullptr;
    const int32_t*  contrib_lminy_q_ = nullptr;
    const int32_t*  contrib_lmaxy_q_ = nullptr;

    // Runtime working buffers
    std::vector<uint32_t> stamp_;
    std::vector<int32_t>  min_x_q_, max_x_q_, min_y_q_, max_y_q_;
    std::vector<uint32_t> touched_nets_;
    uint32_t epoch_ = 1u;
};



