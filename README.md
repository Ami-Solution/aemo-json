nem2json
========

A set of Python scripts to expose NEM data from AEMO into usable formats.

Real time datasets (exposed as JSON):
- current demand and price (day-1 to day+1, 30mn resolution)
- 7-day outlook (forecast for next 7 days, 30mn resolution)

Historic datasets (exposed as database dumps):
- demand (by region, 30mn resolution - since 1998)