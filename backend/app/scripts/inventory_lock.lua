-- KEYS[1]: stock key (e.g. "product:{id}:stock")
-- ARGV[1]: requested quantity (e.g. "1")

local current_stock = redis.call('GET', KEYS[1])

if not current_stock then
    return -1 -- Key does not exist / uninitialized in cache
end

local stock_num = tonumber(current_stock)
local req_qty = tonumber(ARGV[1])

if stock_num >= req_qty then
    local new_stock = redis.call('DECRBY', KEYS[1], req_qty)
    return 1 -- Success: stock reserved
else
    return 0 -- Insufficient stock
end