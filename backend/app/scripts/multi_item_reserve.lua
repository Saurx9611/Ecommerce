-- KEYS: list of stock keys (e.g. "product:1:stock", "product:2:stock")
-- ARGV: list of requested quantities (e.g. "2", "1")

local count = #KEYS

-- 1. Check all keys existence and parse stock
local current_stocks = {}
for i = 1, count do
    local s = redis.call('GET', KEYS[i])
    if not s then
        return {-1, i} -- Uninitialized key at index i
    end
    current_stocks[i] = tonumber(s)
end

-- 2. Check if all items have sufficient inventory
for i = 1, count do
    local req_qty = tonumber(ARGV[i])
    if current_stocks[i] < req_qty then
        return {0, i} -- Insufficient stock for key at index i
    end
end

-- 3. Atomically decrement all items
for i = 1, count do
    local req_qty = tonumber(ARGV[i])
    redis.call('DECRBY', KEYS[i], req_qty)
end

return {1, 0} -- Success: all items atomically reserved
