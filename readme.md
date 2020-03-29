### Using goods server

`curl "http://84.201.157.17:3010/api/v1/goods?query=your_query"`

example:
`curl "http://84.201.157.17:3010/api/v1/goods?query=bionime"`


Response:

``` json
{ // dict, contains "info" and "status"
    "info": [ // list contains list of dicts - each dict represents group of goods
        {
            "group_name": "Ланцет Бионайм №50",
            "items": [
                {
                    "price":410.0,
                    "ship_price":410.0,
                    "shop_name":"Диачек",
                    "title":"Ланцеты Бионайм (Bionime Rightest) GL300 - 50шт",
                    "url":"https://www.diacheck.ru/product/lantsety-bionime-rightest-gl300-50sht"
                },
                ...
            ]
        },
        {
            "group_name": "Прокалыватель Бионайм №50",
            "items": [
                {
                    "price":450.0,
                    "ship_price":450.0,
                    "shop_name":"Диачек",
                    "title":"Прокалыватель БИОНАЙМ Rightest GD 500 (BIONIME,Швейцария)",
                    "url":"https://www.diacheck.ru/product/prokalyvatel-bionaim-rightest-gd-500-bionimeshveitsariya"
                },
            ...
            ],
        }
    ],
    "status": "ok"
}
```
