 """
  Prediction Market Alpha Engine
  """

  import os
  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware
  import httpx

  app = FastAPI(title="Prediction Market Alpha Engine")

  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_methods=["*"],
      allow_headers=["*"],
  )

  # API Keys
  KALSHI_API_KEY = os.environ.get("KALSHI_API_KEY", "")
  NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY", "")
  FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

  @app.get("/")
  async def root():
      return {"app": "Alpha Engine", "status": "live"}

  @app.get("/markets")
  async def get_markets():
      markets = []

      # Kalshi
      try:
          async with httpx.AsyncClient(timeout=15.0) as client:
              resp = await client.get(
                  "https://api.kalshi.com/trade-api/v2/markets";,
                  headers={"Authorization": f"Bearer {KALSHI_API_KEY}"},
                  params={"status": "open", "limit": 100}
              )
              if resp.status_code == 200:
                  for m in resp.json().get("markets", []):
                      price = float(m.get("last_price", 0))
                      markets.append({
                          "id": m.get("id"),
                          "source": "kalshi",
                          "title": m.get("title", m.get("question", "Unknown")),
                          "category": m.get("category", "general").lower(),
                          "price": price,
                          "implied_prob": price / 100.0,
                      })
      except Exception as e:
          print(f"Kalshi error: {e}")

      # Polymarket
      try:
          async with httpx.AsyncClient(timeout=15.0) as client:
              resp = await client.get(
                  "https://clob.polymarket.com/markets";,
                  params={"active": "true", "limit": 100}
              )
              if resp.status_code == 200:
                  for m in resp.json().get("data", []):
                      price = float(m.get("last_price", 0))
                      markets.append({
                          "id": m.get("condition_id"),
                          "source": "polymarket",
                          "title": m.get("question", "Unknown"),
                          "category": m.get("category", "general").lower(),
                          "price": price,
                          "implied_prob": price / 100.0,
                      })
      except Exception as e:
          print(f"Polymarket error: {e}")

      return {"markets": markets, "count": len(markets)}

  @app.get("/divergences")
  async def get_divergences():
      markets_data = await get_markets()
      markets = markets_data.get("markets", [])

      divergences = []
      for m in markets[:20]:
          market_prob = m["implied_prob"]
          ai_prob = 0.5 + (market_prob - 0.5) * 0.85
          div = abs(market_prob - ai_prob)

          if div > 0.03:
              divergences.append({
                  "contract_id": m["id"],
                  "source": m["source"],
                  "title": m["title"],
                  "category": m["category"],
                  "market_prob": round(market_prob, 4),
                  "ai_prob": round(ai_prob, 4),
                  "divergence": round(div, 4),
                  "divergence_pct": round(div * 100, 2),
                  "signal": "buy" if ai_prob > market_prob else "sell",
                  "expected_value": round(div, 4),
              })

      divergences.sort(key=lambda x: x["divergence"], reverse=True)
      return {"divergences": divergences[:10], "count": len(divergences)}

  if __name__ == "__main__":
      import uvicorn
      port = int(os.environ.get("PORT", 8000))
      uvicorn.run(app, host="0.0.0.0", port=port)