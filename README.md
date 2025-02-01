# Shadow: A LangChain-based Portfolio Management Agent

Shadow is an AI-driven portfolio management and token recommendation agent designed to help web3 users monitor, analyze, and optimize their trading strategies automatically. Built using LangChain and powered by state-of-the-art language models, Shadow integrates multiple data sources and analytical agents to provide actionable insights.

> **Note:** This project currently implements **Phase 1**, which focuses on generating recommendations by analyzing social sentiment, technical data, and wallet transaction history. Future phases will extend this functionality to include automated trade execution.

---

## Overview

Shadow leverages several modular agents that each "think" through their tasks by invoking a ChatOpenAI model. These agents work in sequence:
- **XAgent**: Retrieves and analyzes social sentiment data.
- **DexscreenerAgent**: Fetches technical data from the Dexscreener API and analyzes it.
- **WalletAgent**: Analyzes historical wallet transaction data.
- **InsightsAgent**: Consolidates the outputs from the above agents to generate a final, comprehensive recommendation.

Each agent retrieves raw data (either via API calls or simulated data), constructs a prompt, and invokes the model to produce an analysis. This design allows the agents to operate both independently and collaboratively.

---

## Features

- **Social Sentiment Analysis**: Analyzes data from X.com (or similar platforms) to gauge market sentiment.
- **Technical Analysis**: Integrates with the Dexscreener API to retrieve on-chain and chart data and processes it with an LLM.
- **Wallet Transaction Analysis**: Analyzes historical transaction data from a provided wallet address.
- **Consolidated Recommendations**: Combines insights from all agents to produce actionable trading recommendations.
- **Modular and Extensible**: Easily update or replace individual agents as needed.
