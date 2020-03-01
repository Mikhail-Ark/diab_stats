### Using goods server

`curl "http://84.201.157.17:3010/api/v1/goods?query=your_query"`

example:
`curl "http://84.201.157.17:3010/api/v1/goods?query=bionime"`


Response:

``` json
{ // dict, contains "info" and "status"
    "info":[ // list contains list of list (!!!) - each inner list represents group of goods
        [
            {
                "price":410.0,
                "ship_price":0.0,
                "shop_name":"Диачек",
                "title":"Ланцеты Бионайм (Bionime Rightest) GL300 - 50шт",
                "url":"https://www.diacheck.ru/product/lantsety-bionime-rightest-gl300-50sht"
            }
        ],
        [
            {
                "price":450.0,
                "ship_price":0.0,
                "shop_name":"Диачек",
                "title":"Прокалыватель БИОНАЙМ Rightest GD 500 (BIONIME,Швейцария)",
                "url":"https://www.diacheck.ru/product/prokalyvatel-bionaim-rightest-gd-500-bionimeshveitsariya"
            }
        ],
        ...
    ],
    "status":"ok"}
```
