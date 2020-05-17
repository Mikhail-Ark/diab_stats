### Using goods server

`curl -G "http://84.201.157.17:3010/api/v1/goods" --data-urlencode "query=your_query"`

example:
`curl -G "http://84.201.157.17:3010/api/v1/goods" --data-urlencode "query=тест-полоски"`


Response:

``` json
{ // dict, contains "info" and "status"
    "info": [ // list contains list of dicts - each dict represents group of goods
        {
            "group_name": "Ланцет Бионайм №50",
            "fg_id": 7,
            "items": [
                {
                    "price":410.0,
                    "ship_price":410.0,
                    "shop_name":1,
                    "title":"Ланцеты Бионайм (Bionime Rightest) GL300 - 50шт",
                    "url":"https://www.diacheck.ru/product/lantsety-bionime-rightest-gl300-50sht"
                },
                ...
            ]
        },
        {
            "group_name": "Прокалыватель Бионайм №50",
            "fg_id": 7,
            "items": [
                {
                    "price":450.0,
                    "ship_price":450.0,
                    "shop_name":1,
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

Current list of shops:
{
    1: "МедМаг",
    2: "Тест-полоска",
    3: "ДиаКаталог",
    4: "Глюкометр",
    5: "Диабет-контроль",
    6: "Диачек",
    7: "Diabetic Shop",
    8: "Диалайф",
    9: "Diabet Care",
    10: "Diabet Med",
    11: "Diabeta Net",
    12: "Диа-Пульс",
    13: "Диабетон",
    14: "Глюкоза",
    15: "Бетар Компани",
    16: "Диатех",
    17: "Сателлит",
    18: "Diashop 24",
    19: "Диабет Сервис",
    20: "Академия Диабета",
    21: "Диабет Кабинет",
    22: "Жизнь с диабетом",
    23: "Diabet Mag",
    24: "Диабетика",
    25: "Диамарка"
}

Current list of groups (fg_id):
{
    1: "Глюкометры",
    2: "Тест-полоски",
    3: "Инсулиновые помпы",
    4: "Расходные материалы",
    5: "Аксессуары и чехлы",
    6: "Мониторинг глюкозы",
    7: "Ланцеты и прокалыватели",
    8: "Шприц-ручки и иглы",
    9: "Косметика и уход за кожей",
    10: "Витаминные комплексы",
    11: "Средства при гипогликемии",
    12: "Литература",
    13: "Пластыри и дизинфекция",
    14: "Питание",
    15: "Товары для здоровья"
}
