# Alpaca Trading Bot Copilot Instructions

## Project
This is Python-based algorithmic trading system using Alpaca.
The repository contains strategy logic, backtesting, paper trading, market-data handling, and GitHub Actions automation.

## General Rules
- Understand the existing code before modifying it.
- Prefer small, targeted changes over large rewrites.
- Preserve existing behavior unless a change is explicitly requested.
- Do not remove working functionality without explaining why.
- Follow the existing project structure and coding style.
- Use the official Alpaca skills in `.github/skills/` when their workflows are relevant.

## Trading Safety
- Never submit live Alpaca orders.
- Treat all trading changes as paper-trading changes unless I explicitly request otherwise.
- Never expose, print, commit, or hard-code API keys, secrets, or credentials.
- Do not modify GitHub Actions secrets or authentication settings.
- Before changing order logic, clearly explain what orders the new code could generate.
- Prefer deterministic and testable behavior.

## Backtesting
- Avoid look-ahead bias.
- Clearly separate signal time from order-fill time.
- Do not use future bars or future information when generating signals.
- Make assumptions about fills, slippage, fees, splits, dividends, and market hours explicit.
- Keep backtests reproducible.
- When changing strategy logic, identify how the change affects historical results.

## Multiple Strategies
- Understand the existing strategies before adding a new one.
- Understand when a new strategy is appropriate versus modifying an existing one. If a new strategy is appropriate, explain why. If unsure wether or not to create a new strategy, ask for guidance.
- Never create a new strategy without first requesting approval.
- Never mixing multiple strategies in the same code.
- When adding a new strategy, create a new folder for it's backtesting components under the backtesting directory and trading components under the algorithm directory.
- Each strategy will have it's own paper trading account and Alpaca API keys. Ensure that the correct keys are used for each strategy.
- When adding a new strategy, create a new GitHub Actions workflow for it. The workflow should be named after the strategy and should be located in the `.github/workflows/` directory.
- Current Strategies:
  - BIBO

## BIBO Strategy
When working on BIBO, pay particular attention to:
- SMA indicators
- ATR
- SPY market-regime filtering
- Relative strength versus SPY
- Volume ranking
- Position sizing
- Stop losses
- Take profits
- Earnings avoidance
- Alpaca order handling

## Before Making Significant Changes
First explain:
1. What you found in the existing code.
2. What you propose changing.
3. Which files will change.
4. Any potential risks or unintended behavior.

For significant changes, use Plan mode first when appropriate.

## Testing
- Run relevant tests or backtests after making changes.
- Report errors rather than silently working around them.
- Do not claim a change works unless it has been tested.