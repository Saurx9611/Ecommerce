-- Sliding Window Rate Limiter Lua Script
-- KEYS[1]: Rate limit key (e.g., "rate_limit:auth_login:127.0.0.1")
-- ARGV[1]: Current epoch timestamp in milliseconds
-- ARGV[2]: Window size in milliseconds
-- ARGV[3]: Max allowed requests within window

local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local max_limit = tonumber(ARGV[3])

local clear_before = now - window

-- 1. Remove entries older than the rolling window
redis.call('ZREMRANGEBYSCORE', key, '-inf', clear_before)

-- 2. Count requests currently in the window
local current_count = redis.call('ZCARD', key)

if current_count < max_limit then
    -- 3. Add current request with millisecond precision
    redis.call('ZADD', key, now, tostring(now) .. ':' .. redis.call('INCR', key .. ':seq'))
    -- 4. Expire key slightly after window expires
    local ttl_seconds = math.ceil(window / 1000) + 2
    redis.call('EXPIRE', key, ttl_seconds)
    redis.call('EXPIRE', key .. ':seq', ttl_seconds)
    
    return {1, current_count + 1, max_limit, 0} -- {is_allowed (1=true), current_count, max_limit, retry_after}
else
    -- 5. Calculate retry_after from oldest timestamp in window
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local retry_after = 1
    if oldest and #oldest >= 2 then
        local oldest_time = tonumber(oldest[2])
        retry_after = math.max(1, math.ceil((oldest_time + window - now) / 1000))
    end
    
    return {0, current_count, max_limit, retry_after} -- {is_allowed (0=false), current_count, max_limit, retry_after}
end
