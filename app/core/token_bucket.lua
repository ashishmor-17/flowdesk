local key = KEYS[1]

local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local requested = tonumber(ARGV[3])
local now = tonumber(ARGV[4])

local bucket = redis.call("HMGET", key, "tokens", "timestamp")

local tokens = tonumber(bucket[1])
local timestamp = tonumber(bucket[2])

if tokens == nil then
    tokens = capacity
    timestamp = now
end

local elapsed = now - timestamp
local refill = elapsed * refill_rate

tokens = math.min(
    capacity,
    tokens + refill
)

local allowed = 0

if tokens >= requested then
    tokens = tokens - requested
    allowed = 1
end

redis.call(
    "HMSET",
    key,
    "tokens",
    tokens,
    "timestamp",
    now
)

redis.call(
    "EXPIRE",
    key,
    math.ceil(capacity / refill_rate)
)

return {
    allowed,
    tokens
}