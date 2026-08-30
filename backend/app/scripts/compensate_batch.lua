-- KEYS: list of stock keys (e.g. "product:1:stock", "product:2:stock")
-- ARGV: list of quantities to refund (e.g. "2", "1")

local count = #KEYS

for i = 1, count do
    local exists = redis.call('EXISTS', KEYS[i])
    if exists == 1 then
        local req_qty = tonumber(ARGV[i])
        redis.call('INCRBY', KEYS[i], req_qty)
    end
end

return 1
