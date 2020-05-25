import jqdatasdk
jqdatasdk.auth("15814765423", "Mast3rch@hk")

result = jqdatasdk.get_price("000001.XSHE")
print(result)