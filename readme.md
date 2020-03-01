### Using goods server

`curl "http://84.201.157.17:3010/api/v1/goods?query=bionime"`

Response:

``` json
{ // dict, contains "info" and "status"
    "info":[ // list contains list of list (!!!) - each inner list represents group of goods
        [
            {
                "price":1175.0,
                "ship_price":1175.0,
                "shop_name":"МедМаг",
                "title":"Глюкометр Сателлит Плюс",
                "url":"https://www.medmag.ru/index.php?productID=729"
            },
            {
                "price":1350.0,
                "ship_price":NaN,
                "shop_name":"Тест-полоска",
                "title":"Глюкометр Элта Сателлит Плюс",
                "url":"http://www.test-poloska.ru/catalog/bloodmeters/eltasatelliteplus.html"
            },
            ...
        ]
    ],
    "status":"ok"}
```
