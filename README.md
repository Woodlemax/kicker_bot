# KickerBot

## Telegram bot
@NxKickerBot

## Мониторинг занятости кикера (grafana)
http://grafana:8081/d/osEOCNsZk/kicker?orgId=1&refresh=5s

## Начинка
* Корпус
Печать на 3D принтере (PLA)
<img src=/other_files/case.png width="400" />
Файлы:

[Base_1](other_files/Base_1.stl)

[Base_2](other_files/Base_2.stl)

[Inner](other_files/Inner.stl)

* Начинка
<img src=/other_files/real_body.png width="400" />
	1. 18650 - 3400mAh
	2. Плата зарядки
	3. LoLin V3 NodeMcu
	4. Датчик удара

## Алгоритм работы
1. Включается
2. Подключается к сети
3. Отсылает в InfluxDB - Жив
4. Считывает с датчика удара активность (в течении 1 секунды)
	* Активность есть
		* Отсылает в InfluxDB - Есть активность
		* Повторяет пункт 4
	* Активности нет
		* Засыпает на 60 секунд
		* Переходит к пункту 1
