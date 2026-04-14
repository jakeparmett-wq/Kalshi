 """
  Prediction Market Alpha Engine - Minimal Version
  """

  import os
  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware

  app = FastAPI(title="Prediction Market Alpha Engine")

  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )

  # API Keys from your .env
  KALSHI_API_KEY = "5a02016d-7446-45ba-9890-2973a521d878"
  NEWSAPI_KEY = "8247cf75edb94a568bb45cf2d3b0f9da"
  FRED_API_KEY = "49f08dc8eb80282deda36c7f8409066e"

  @app.get("/")
  async def root():
      return {
          "app": "Prediction Market Alpha Engine",
          "status": "running",
          "endpoints": ["/markets", "/divergences"]
      }

  @app.get("/markets")
  async def get_markets():
      """Fetch live markets from Kalshi and Polymarket"""
      import httpx

      markets = []

      # Kalshi
      try:
          async with httpx.AsyncClient(timeout=10.0) as client:
              resp = await client.get(
                  "https://api.kalshi.com/trade-api/v2/markets";,
                  headers={"Authorization": f"Bearer {KALSHI_API_KEY}"},
                  params={"status": "open", "limit": 50}
              )
              if resp.status_code == 200:
                  data = resp.json()
                  for m in data.get("markets", []):
                      markets.append({
                          "id": m.get("id"),
                          "source": "kalshi",
                          "title": m.get("title", m.get("question", "Unknown")),
                          "category": m.get("category", "general"),
                          "price": float(m.get("last_price", 0)),
                          "implied_prob": float(m.get("last_price", 0)) / 100.0,
                      })
      except Exception as e:
          print(f"Kalshi error: {e}")

      # Polymarket
      try:
          async with httpx.AsyncClient(timeout=10.0) as client:
              resp = await client.get(
                  "https://clob.polymarket.com/markets";,
                  params={"active": "true", "limit": 50}
              )
              if resp.status_code == 200:
                  data = resp.json()
                  for m in data.get("data", []):
                      markets.append({
                          "id": m.get("condition_id"),
                          "source": "polymarket",
                          "title": m.get("question", "Unknown"),
                          "category": m.get("category", "general"),
                          "price": float(m.get("last_price", 0)),
                          "implied_prob": float(m.get("last_price", 0)) / 100.0,
                      })
      except Exception as e:
          print(f"Polymarket error: {e}")

      return {"markets": markets, "count": len(markets)}

  @app.get("/divergences")
  async def get_divergences():
      """Get contracts with significant price divergences"""
      markets_resp = await get_markets()
      markets = markets_resp.get("markets", [])

      # Simple divergence: high price variance between sources for same topic
      divergences = []

      # For now, return top 10 by implied probability difference from 0.5
      for m in sorted(markets, key=lambda x: abs(x["implied_prob"] - 0.5), reverse=True)[:10]:
          divergences.append({
              "contract_id": m["id"],
              "source": m["source"],
              "title": m["title"],
              "market_prob": m["implied_prob"],
              "ai_prob": 0.5 + (m["implied_prob"] - 0.5) * 0.8,  # Simple model
              "divergence": abs(m["implied_prob"] - (0.5 + (m["implied_prob"] - 0.5) * 0.8)),
              "signal": "buy" if m["implied_prob"] < 0.5 else "sell",
              "category": m["category"],
          })

      return {"divergences": divergences, "count": len(divergences)}

  if __name__ == "__main__":
      import uvicorn
      port = int(os.environ.get("PORT", 8000))
      uvicorn.run(app, host="0.0.0.0", port=port)
