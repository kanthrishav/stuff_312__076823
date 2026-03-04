#pragma once

#include <cstdint>
#include <vector>
#include <string>
#include <unordered_map>
#include <stdexcept>
#include <limits>
#include <cmath>
#include <algorithm>
#include <cstring>

#include <nlohmann/json.hpp>

// ============================================================
// Stage A: Preprocessing (independent namespace)
// ============================================================
namespace hpwl_preprocess {

struct hpwl_preprocess_options final {
  // Fixed-point scale for 4 decimal points.
  int32_t fp_scale = 10000;

  // If your input text has trailing commas (like the provided template),
  // set this true when using preprocess_json_text().
  bool allow_trailing_commas_via_sanitize = false;
};

namespace detail {

// Minimal sanitizer: removes commas before ']' or '}'.
// This is NOT a full JSON5 parser; it only targets the common "trailing comma" case.
inline std::string sanitize_trailing_commas(const std::string& s) {
  std::string out;
  out.reserve(s.size());

  for (size_t i = 0; i < s.size(); ++i) {
    char c = s[i];
    if (c == ',') {
      // Look ahead for next non-space
      size_t j = i + 1;
      while (j < s.size() && (s[j] == ' ' || s[j] == '\t' || s[j] == '\r' || s[j] == '\n')) ++j;
      if (j < s.size() && (s[j] == ']' || s[j] == '}')) {
        // skip this comma
        continue;
      }
    }
    out.push_back(c);
  }
  return out;
}

template <typename T>
inline void append_pod(std::vector<std::uint8_t>& dst, const T& v) {
  static_assert(std::is_trivially_copyable<T>::value, "pod only");
  const std::uint8_t* p = reinterpret_cast<const std::uint8_t*>(&v);
  dst.insert(dst.end(), p, p + sizeof(T));
}

inline void append_bytes(std::vector<std::uint8_t>& dst, const void* data, size_t n) {
  const std::uint8_t* p = reinterpret_cast<const std::uint8_t*>(data);
  dst.insert(dst.end(), p, p + n);
}

inline int32_t to_fp(float x, int32_t s) {
  // exact to 4dp if inputs are already <= 4dp and scale=1e4
  return static_cast<int32_t>(std::llround(static_cast<double>(x) * static_cast<double>(s)));
}

} // namespace detail

// Binary layout (little-endian, POD):
// [header]
// [block_meta * blocks]
// [variant_meta * variants]
// [pin_record * pins]
//
// No strings in the blob: runtime doesn't need them for HPWL.

class hpwl_preprocessor final {
public:
  static std::vector<std::uint8_t> preprocess_json(
      const nlohmann::json& j_block,
      const hpwl_preprocess_options& opt = {}) {

    if (!j_block.is_object()) {
      throw std::runtime_error("j_block must be a JSON object at top level");
    }

    // ---- Determine a deterministic block ordering (sorted keys) ----
    std::vector<std::string> block_names;
    block_names.reserve(j_block.size());
    for (auto it = j_block.begin(); it != j_block.end(); ++it) {
      block_names.push_back(it.key());
    }
    std::sort(block_names.begin(), block_names.end());

    // ---- Net string -> dense net_id ----
    // Reserve heuristic: blocks * variants * nets_per_variant (rough).
    std::unordered_map<std::string, std::uint32_t> net_to_id;
    net_to_id.reserve(static_cast<size_t>(block_names.size()) * 64);

    struct block_meta { std::uint32_t variant_begin; std::uint16_t variant_count; std::uint16_t pad; };
    struct variant_meta { std::uint32_t pin_begin; std::uint32_t pin_count; };
    struct pin_record { std::uint32_t net_id; std::int32_t lx_fp; std::int32_t ly_fp; };

    std::vector<block_meta> blocks;
    std::vector<variant_meta> variants;
    std::vector<pin_record> pins;

    blocks.reserve(block_names.size());

    auto get_net_id = [&](const std::string& net_name) -> std::uint32_t {
      auto it = net_to_id.find(net_name);
      if (it != net_to_id.end()) return it->second;
      const std::uint32_t id = static_cast<std::uint32_t>(net_to_id.size());
      net_to_id.emplace(net_name, id);
      return id;
    };

    // ---- Parse ----
    for (const auto& block_name : block_names) {
      const auto& var_list = j_block.at(block_name);
      if (!var_list.is_array()) {
        throw std::runtime_error("block '" + block_name + "' must map to an array of variants");
      }

      block_meta bm{};
      bm.variant_begin = static_cast<std::uint32_t>(variants.size());
      bm.variant_count = static_cast<std::uint16_t>(var_list.size());
      bm.pad = 0;

      // If >65535 variants per block, widen; your stated max is 100.
      if (var_list.size() > std::numeric_limits<std::uint16_t>::max()) {
        throw std::runtime_error("too many variants in block '" + block_name + "'");
      }

      for (size_t v = 0; v < var_list.size(); ++v) {
        const auto& var = var_list[v];
        if (!var.is_object()) {
          throw std::runtime_error("variant must be an object (block '" + block_name + "')");
        }

        variant_meta vm{};
        vm.pin_begin = static_cast<std::uint32_t>(pins.size());
        vm.pin_count = 0;

        if (!var.contains("nets")) {
          // variant with no nets -> allowed, contributes nothing
          variants.push_back(vm);
          continue;
        }

        const auto& nets = var.at("nets");

        // Expected schema (as in your template): nets is an object: net_name -> pin_list
        if (!nets.is_object()) {
          throw std::runtime_error("'nets' must be an object: net_name -> [pins...]");
        }

        for (auto nit = nets.begin(); nit != nets.end(); ++nit) {
          const std::string& net_name = nit.key();
          const std::uint32_t net_id = get_net_id(net_name);

          const auto& pin_list = nit.value();
          if (!pin_list.is_array()) {
            throw std::runtime_error("net '" + net_name + "' must map to an array of pin dicts");
          }

          for (const auto& pin : pin_list) {
            if (!pin.is_object() || !pin.contains("__x")) {
              throw std::runtime_error("pin must be an object containing '__x'");
            }
            const auto& xy = pin.at("__x");
            if (!xy.is_array() || xy.size() != 2) {
              throw std::runtime_error("'__x' must be [x,y]");
            }

            const float lx = xy[0].get<float>();
            const float ly = xy[1].get<float>();

            pin_record pr{};
            pr.net_id = net_id;
            pr.lx_fp = detail::to_fp(lx, opt.fp_scale);
            pr.ly_fp = detail::to_fp(ly, opt.fp_scale);
            pins.push_back(pr);
            ++vm.pin_count;
          }
        }

        variants.push_back(vm);
      }

      blocks.push_back(bm);
    }

    // ---- Emit blob ----
    struct header {
      std::uint32_t magic;      // 'HPWL'
      std::uint32_t version;    // 1
      std::uint32_t fp_scale;   // 10000
      std::uint32_t blocks_count;
      std::uint32_t variants_count;
      std::uint32_t pins_count;
      std::uint32_t nets_count;
    };

    header h{};
    h.magic = 0x4C575048u; // 'H''P''W''L' little-endian
    h.version = 1;
    h.fp_scale = static_cast<std::uint32_t>(opt.fp_scale);
    h.blocks_count = static_cast<std::uint32_t>(blocks.size());
    h.variants_count = static_cast<std::uint32_t>(variants.size());
    h.pins_count = static_cast<std::uint32_t>(pins.size());
    h.nets_count = static_cast<std::uint32_t>(net_to_id.size());

    std::vector<std::uint8_t> blob;
    blob.reserve(sizeof(header)
                 + blocks.size() * sizeof(block_meta)
                 + variants.size() * sizeof(variant_meta)
                 + pins.size() * sizeof(pin_record));

    detail::append_pod(blob, h);
    detail::append_bytes(blob, blocks.data(), blocks.size() * sizeof(block_meta));
    detail::append_bytes(blob, variants.data(), variants.size() * sizeof(variant_meta));
    detail::append_bytes(blob, pins.data(), pins.size() * sizeof(pin_record));

    return blob;
  }

  // Convenience: parse JSON text (optionally sanitizing trailing commas) then preprocess.
  static std::vector<std::uint8_t> preprocess_json_text(
      const std::string& json_text,
      const hpwl_preprocess_options& opt = {}) {

    std::string text = json_text;
    if (opt.allow_trailing_commas_via_sanitize) {
      text = detail::sanitize_trailing_commas(text);
    }
    const auto j = nlohmann::json::parse(text);
    return preprocess_json(j, opt);
  }
};

} // namespace hpwl_preprocess

// ============================================================
// Stage B + C: Runtime evaluator (separate namespace)
// ============================================================
namespace hpwl_runtime {

class hpwl_evaluator final {
public:
  hpwl_evaluator() = default;

  // Stage B: initialization (public)
  void initialize_from_blob(const std::vector<std::uint8_t>& blob) {
    reset();

    if (blob.size() < sizeof(header_)) {
      throw std::runtime_error("hpwl blob too small");
    }

    size_t off = 0;
    header_ = read_pod<header>(blob, off);

    if (header_.magic != 0x4C575048u || header_.version != 1) {
      throw std::runtime_error("hpwl blob header mismatch");
    }

    fp_scale_ = static_cast<int32_t>(header_.fp_scale);

    blocks_.resize(header_.blocks_count);
    variants_.resize(header_.variants_count);
    pins_.resize(header_.pins_count);

    read_array(blob, off, blocks_.data(), blocks_.size());
    read_array(blob, off, variants_.data(), variants_.size());
    read_array(blob, off, pins_.data(), pins_.size());

    nets_count_ = header_.nets_count;

    // Allocate net extents and epoch arrays (hot path state)
    net_min_x_.resize(nets_count_);
    net_max_x_.resize(nets_count_);
    net_min_y_.resize(nets_count_);
    net_max_y_.resize(nets_count_);
    net_epoch_.assign(nets_count_, 0u);

    // Temps
    block_x_fp_.resize(blocks_.size());
    block_y_fp_.resize(blocks_.size());

    touched_nets_.reserve(std::min<std::uint32_t>(nets_count_, 1'000u));

    epoch_ = 1;
  }

  // Public wrapper the optimizer can call; the hot path itself is private.
  float evaluate_hpwl(
      const float* block_center_x,
      const float* block_center_y,
      const std::uint16_t* selected_variant_per_block) {
    return compute_hpwl_hot_path(block_center_x, block_center_y, selected_variant_per_block);
  }

  std::uint32_t blocks_count() const noexcept { return static_cast<std::uint32_t>(blocks_.size()); }
  std::uint32_t nets_count() const noexcept { return nets_count_; }
  int32_t fp_scale() const noexcept { return fp_scale_; }

private:
  // ---------- Blob POD types ----------
  struct header {
    std::uint32_t magic;
    std::uint32_t version;
    std::uint32_t fp_scale;
    std::uint32_t blocks_count;
    std::uint32_t variants_count;
    std::uint32_t pins_count;
    std::uint32_t nets_count;
  };

  struct block_meta { std::uint32_t variant_begin; std::uint16_t variant_count; std::uint16_t pad; };
  struct variant_meta { std::uint32_t pin_begin; std::uint32_t pin_count; };
  struct pin_record { std::uint32_t net_id; std::int32_t lx_fp; std::int32_t ly_fp; };

  template <typename T>
  static T read_pod(const std::vector<std::uint8_t>& blob, size_t& off) {
    if (off + sizeof(T) > blob.size()) throw std::runtime_error("hpwl blob truncated");
    T v;
    std::memcpy(&v, blob.data() + off, sizeof(T));
    off += sizeof(T);
    return v;
  }

  template <typename T>
  static void read_array(const std::vector<std::uint8_t>& blob, size_t& off, T* dst, size_t count) {
    const size_t bytes = count * sizeof(T);
    if (off + bytes > blob.size()) throw std::runtime_error("hpwl blob truncated (array)");
    std::memcpy(dst, blob.data() + off, bytes);
    off += bytes;
  }

  static inline std::int32_t to_fp(float x, int32_t s) noexcept {
    return static_cast<std::int32_t>(std::llround(static_cast<double>(x) * static_cast<double>(s)));
  }

  // Stage C: hot path (private)
  float compute_hpwl_hot_path(
      const float* block_center_x,
      const float* block_center_y,
      const std::uint16_t* selected_variant_per_block) {

    const std::uint32_t b_count = static_cast<std::uint32_t>(blocks_.size());
    if (b_count == 0) return 0.0f;

    // New epoch: O(#touched_nets) reset, not O(total_nets)
    ++epoch_;
    if (epoch_ == 0) { // wraparound (extremely rare)
      std::fill(net_epoch_.begin(), net_epoch_.end(), 0u);
      epoch_ = 1;
    }
    touched_nets_.clear();

    // Convert block centers to fixed-point (B multiplications, small)
    for (std::uint32_t b = 0; b < b_count; ++b) {
      block_x_fp_[b] = to_fp(block_center_x[b], fp_scale_);
      block_y_fp_[b] = to_fp(block_center_y[b], fp_scale_);
    }

    // Core: touch each active pin exactly once
    for (std::uint32_t b = 0; b < b_count; ++b) {
      const block_meta& bm = blocks_[b];
      std::uint16_t v_local = selected_variant_per_block[b];

      // Defensive clamp; for max speed you can compile-time disable this check.
      if (v_local >= bm.variant_count) v_local = static_cast<std::uint16_t>(bm.variant_count ? (bm.variant_count - 1) : 0);

      const std::uint32_t v_global = bm.variant_begin + static_cast<std::uint32_t>(v_local);
      const variant_meta& vm = variants_[v_global];

      const std::int32_t base_x = block_x_fp_[b];
      const std::int32_t base_y = block_y_fp_[b];

      const std::uint32_t p0 = vm.pin_begin;
      const std::uint32_t p1 = p0 + vm.pin_count;

      for (std::uint32_t p = p0; p < p1; ++p) {
        const pin_record& pr = pins_[p];
        const std::uint32_t n = pr.net_id;

        const std::int32_t gx = base_x + pr.lx_fp;
        const std::int32_t gy = base_y + pr.ly_fp;

        if (net_epoch_[n] != epoch_) {
          net_epoch_[n] = epoch_;
          net_min_x_[n] = gx; net_max_x_[n] = gx;
          net_min_y_[n] = gy; net_max_y_[n] = gy;
          touched_nets_.push_back(n);
        } else {
          // branchless-ish min/max (compilers typically lower to cmov/min/max)
          if (gx < net_min_x_[n]) net_min_x_[n] = gx;
          if (gx > net_max_x_[n]) net_max_x_[n] = gx;
          if (gy < net_min_y_[n]) net_min_y_[n] = gy;
          if (gy > net_max_y_[n]) net_max_y_[n] = gy;
        }
      }
    }

    // Sum HPWL over touched nets only
    std::int64_t hpwl_sum_fp = 0;
    for (std::uint32_t i = 0; i < static_cast<std::uint32_t>(touched_nets_.size()); ++i) {
      const std::uint32_t n = touched_nets_[i];
      hpwl_sum_fp += static_cast<std::int64_t>(net_max_x_[n] - net_min_x_[n])
                  + static_cast<std::int64_t>(net_max_y_[n] - net_min_y_[n]);
    }

    return static_cast<float>(static_cast<double>(hpwl_sum_fp) / static_cast<double>(fp_scale_));
  }

  void reset() {
    blocks_.clear();
    variants_.clear();
    pins_.clear();
    net_min_x_.clear(); net_max_x_.clear(); net_min_y_.clear(); net_max_y_.clear();
    net_epoch_.clear();
    touched_nets_.clear();
    block_x_fp_.clear();
    block_y_fp_.clear();
    nets_count_ = 0;
    fp_scale_ = 10000;
    epoch_ = 1;
    header_ = {};
  }

private:
  header header_{};

  std::vector<block_meta> blocks_;
  std::vector<variant_meta> variants_;
  std::vector<pin_record> pins_;

  std::uint32_t nets_count_ = 0;
  int32_t fp_scale_ = 10000;

  // Hot-path state (per net)
  std::vector<std::int32_t> net_min_x_, net_max_x_, net_min_y_, net_max_y_;
  std::vector<std::uint32_t> net_epoch_;
  std::vector<std::uint32_t> touched_nets_;
  std::uint32_t epoch_ = 1;

  // Temp per iteration (per block)
  std::vector<std::int32_t> block_x_fp_, block_y_fp_;
};

} // namespace hpwl_runtime