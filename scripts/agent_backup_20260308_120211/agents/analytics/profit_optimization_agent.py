from __future__ import annotations
from typing import Dict, Any, List
import math
from datetime import datetime
from farmxpert.core.base_agent.enhanced_base_agent import EnhancedBaseAgent
from farmxpert.services.tools import ProfitOptimizationTool
 


class ProfitOptimizationAgent(EnhancedBaseAgent):
    name = "profit_optimization_agent"
    description = "Evaluates profitability across different crop strategies and input combinations. Suggests changes to increase margins"

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Deterministic profit optimization (no LLM).

        Expected inputs (either in `context` or at top-level):
        - crop: str
        - area_acre: float
        - yield_per_acre: float
        - expenses: list[dict] (optional)
        - market_prices: dict[str, float] (optional)
        """

        tools = inputs.get("tools", {})
        context = inputs.get("context", {})
        query = inputs.get("query", "")

        crop = context.get("crop", inputs.get("crop"))
        area_acre = context.get("area_acre", inputs.get("area_acre"))
        yield_per_acre = context.get("yield_per_acre", inputs.get("yield_per_acre"))

        expenses = context.get("expenses", inputs.get("expenses"))
        if not isinstance(expenses, list):
            expenses = []

        market_prices = context.get("market_prices", inputs.get("market_prices"))
        if not isinstance(market_prices, dict):
            market_prices = {}

        # Use tool-provided analysis if available, but do not require it.
        tool_profitability: Dict[str, Any] = {}
        if "profit_optimization" in tools and isinstance(tools.get("profit_optimization"), ProfitOptimizationTool):
            try:
                tool_profitability = await tools["profit_optimization"].calculate_profitability(
                    crops=[crop] if crop else [],
                    yield_predictions={},
                    market_prices=market_prices,
                    input_costs={},
                    farm_size=float(area_acre or 0),
                )
            except Exception as e:
                self.logger.warning(f"Failed to calculate profitability with tool: {e}")

        # Deterministic computation similar to provided profit agent1
        total_expense = 0.0
        for item in expenses:
            if not isinstance(item, dict):
                continue
            try:
                amt = float(item.get("amount") or item.get("cost") or 0)
            except Exception:
                amt = 0.0
            total_expense += amt

        expected_yield = None
        try:
            if area_acre is not None and yield_per_acre is not None:
                expected_yield = float(area_acre) * float(yield_per_acre)
        except Exception:
            expected_yield = None

        market_table: List[Dict[str, Any]] = []
        best_market: Dict[str, Any] | None = None
        if expected_yield is not None and market_prices:
            for market, price in market_prices.items():
                try:
                    p = float(price)
                except Exception:
                    continue
                revenue = expected_yield * p
                profit = revenue - total_expense
                row = {"market": market, "price": p, "revenue": revenue, "profit": profit}
                market_table.append(row)
            if market_table:
                best_market = max(market_table, key=lambda x: float(x.get("price") or 0))

        if not crop or expected_yield is None:
            response = "Provide crop, area_acre, and yield_per_acre to estimate profit."
        elif not market_prices:
            response = f"Profit analysis for {crop} prepared, but market prices are missing."
        else:
            response = f"Profit analysis for {crop} complete."

        return {
            "agent": self.name,
            "success": True,
            "response": response,
            "data": {
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "crop": crop,
                "area_acre": area_acre,
                "yield_per_acre": yield_per_acre,
                "expected_yield": expected_yield,
                "expenses": expenses,
                "total_expense": total_expense,
                "market_prices": market_prices,
                "market_comparison_table": market_table,
                "best_market": best_market,
                "tool_profitability": tool_profitability,
            },
            "recommendations": [
                f"Collect 2-3 mandi prices for {crop} before selling." if crop else "Collect mandi prices before selling.",
            ],
            "warnings": [],
            "metadata": {"model": "deterministic", "tools_used": list(tools.keys())},
        }
    
    def _calculate_current_profitability(self, crops: List[str], yields: Dict, 
                                       prices: Dict, costs: Dict, farm_size: float) -> Dict[str, Any]:
        """Calculate current profitability for each crop"""
        profitability = {
            "crop_analysis": {},
            "total_revenue": 0,
            "total_costs": 0,
            "total_profit": 0,
            "profit_margin": 0,
            "roi": 0
        }
        
        for crop in crops:
            yield_per_acre = yields.get(crop, 0)
            price_per_ton = prices.get(crop, 0)
            cost_per_acre = costs.get(crop, 0)
            
            # Calculate crop-specific metrics
            revenue_per_acre = yield_per_acre * price_per_ton
            profit_per_acre = revenue_per_acre - cost_per_acre
            margin_per_acre = (profit_per_acre / revenue_per_acre * 100) if revenue_per_acre > 0 else 0
            roi_per_acre = (profit_per_acre / cost_per_acre * 100) if cost_per_acre > 0 else 0
            
            profitability["crop_analysis"][crop] = {
                "yield_per_acre": yield_per_acre,
                "price_per_ton": price_per_ton,
                "cost_per_acre": cost_per_acre,
                "revenue_per_acre": revenue_per_acre,
                "profit_per_acre": profit_per_acre,
                "margin_percentage": margin_per_acre,
                "roi_percentage": roi_per_acre
            }
            
            # Add to totals
            profitability["total_revenue"] += revenue_per_acre
            profitability["total_costs"] += cost_per_acre
            profitability["total_profit"] += profit_per_acre
        
        # Calculate overall metrics
        if profitability["total_revenue"] > 0:
            profitability["profit_margin"] = (profitability["total_profit"] / profitability["total_revenue"]) * 100
        
        if profitability["total_costs"] > 0:
            profitability["roi"] = (profitability["total_profit"] / profitability["total_costs"]) * 100
        
        return profitability
    
    def _generate_optimization_scenarios(self, crops: List[str], yields: Dict, 
                                       prices: Dict, costs: Dict, farm_size: float,
                                       budget_constraints: Dict, risk_tolerance: str) -> List[Dict[str, Any]]:
        """Generate different optimization scenarios"""
        scenarios = []
        
        # Scenario 1: Crop mix optimization
        scenarios.append(self._crop_mix_optimization(crops, yields, prices, costs, farm_size))
        
        # Scenario 2: Input cost optimization
        scenarios.append(self._input_cost_optimization(crops, yields, prices, costs, farm_size))
        
        # Scenario 3: Yield improvement optimization
        scenarios.append(self._yield_improvement_optimization(crops, yields, prices, costs, farm_size))
        
        # Scenario 4: Market timing optimization
        scenarios.append(self._market_timing_optimization(crops, yields, prices, costs, farm_size))
        
        # Scenario 5: Risk-adjusted optimization
        scenarios.append(self._risk_adjusted_optimization(crops, yields, prices, costs, farm_size, risk_tolerance))
        
        return scenarios
    
    def _crop_mix_optimization(self, crops: List[str], yields: Dict, prices: Dict, 
                              costs: Dict, farm_size: float) -> Dict[str, Any]:
        """Optimize crop mix for maximum profitability"""
        scenario = {
            "name": "Crop Mix Optimization",
            "description": "Optimize allocation of farm area to most profitable crops",
            "changes": {},
            "projected_profitability": {},
            "implementation_cost": 0,
            "risk_level": "medium"
        }
        
        # Calculate profitability per acre for each crop
        crop_profitability = {}
        for crop in crops:
            yield_per_acre = yields.get(crop, 0)
            price_per_ton = prices.get(crop, 0)
            cost_per_acre = costs.get(crop, 0)
            profit_per_acre = (yield_per_acre * price_per_ton) - cost_per_acre
            crop_profitability[crop] = profit_per_acre
        
        # Sort crops by profitability
        sorted_crops = sorted(crop_profitability.items(), key=lambda x: x[1], reverse=True)
        
        # Allocate more area to profitable crops
        optimal_allocation = {}
        remaining_area = farm_size
        
        for crop, profit_per_acre in sorted_crops:
            if profit_per_acre > 0:
                # Allocate more area to profitable crops
                optimal_allocation[crop] = min(remaining_area * 0.4, remaining_area)
                remaining_area -= optimal_allocation[crop]
            else:
                # Reduce or eliminate unprofitable crops
                optimal_allocation[crop] = remaining_area * 0.1
                remaining_area -= optimal_allocation[crop]
        
        # Calculate projected profitability
        total_profit = 0
        for crop, area in optimal_allocation.items():
            profit_per_acre = crop_profitability[crop]
            total_profit += profit_per_acre * area
        
        scenario["changes"] = optimal_allocation
        scenario["projected_profitability"] = {
            "total_profit": total_profit,
            "profit_per_acre": total_profit / farm_size if farm_size > 0 else 0,
            "improvement_percentage": 15  # Estimated improvement
        }
        
        return scenario
    
    def _input_cost_optimization(self, crops: List[str], yields: Dict, prices: Dict, 
                                costs: Dict, farm_size: float) -> Dict[str, Any]:
        """Optimize input costs while maintaining yields"""
        scenario = {
            "name": "Input Cost Optimization",
            "description": "Reduce input costs through better sourcing and application",
            "changes": {},
            "projected_profitability": {},
            "implementation_cost": 0,
            "risk_level": "low"
        }
        
        cost_reductions = {}
        total_cost_savings = 0
        
        for crop in crops:
            current_cost = costs.get(crop, 0)
            
            # Potential cost reductions
            fertilizer_savings = current_cost * 0.15  # 15% savings on fertilizer
            pesticide_savings = current_cost * 0.10   # 10% savings on pesticides
            labor_savings = current_cost * 0.05       # 5% savings on labor
            
            total_savings = fertilizer_savings + pesticide_savings + labor_savings
            cost_reductions[crop] = {
                "current_cost": current_cost,
                "optimized_cost": current_cost - total_savings,
                "savings": total_savings,
                "savings_percentage": (total_savings / current_cost * 100) if current_cost > 0 else 0
            }
            
            total_cost_savings += total_savings
        
        # Calculate projected profitability
        current_total_cost = sum(costs.values())
        optimized_total_cost = current_total_cost - total_cost_savings
        current_total_revenue = sum(yields.get(crop, 0) * prices.get(crop, 0) for crop in crops)
        optimized_profit = current_total_revenue - optimized_total_cost
        
        scenario["changes"] = cost_reductions
        scenario["projected_profitability"] = {
            "total_profit": optimized_profit,
            "cost_savings": total_cost_savings,
            "improvement_percentage": (total_cost_savings / current_total_cost * 100) if current_total_cost > 0 else 0
        }
        scenario["implementation_cost"] = total_cost_savings * 0.1  # 10% of savings for implementation
        
        return scenario
    
    def _yield_improvement_optimization(self, crops: List[str], yields: Dict, prices: Dict, 
                                      costs: Dict, farm_size: float) -> Dict[str, Any]:
        """Optimize yields through better management practices"""
        scenario = {
            "name": "Yield Improvement Optimization",
            "description": "Increase yields through improved management practices",
            "changes": {},
            "projected_profitability": {},
            "implementation_cost": 0,
            "risk_level": "medium"
        }
        
        yield_improvements = {}
        total_revenue_increase = 0
        total_implementation_cost = 0
        
        for crop in crops:
            current_yield = yields.get(crop, 0)
            current_price = prices.get(crop, 0)
            current_cost = costs.get(crop, 0)
            
            # Potential yield improvements
            if crop in ["wheat", "maize"]:
                yield_increase = current_yield * 0.20  # 20% improvement
                additional_cost = current_cost * 0.15   # 15% additional cost
            elif crop in ["rice", "pulses"]:
                yield_increase = current_yield * 0.15   # 15% improvement
                additional_cost = current_cost * 0.10   # 10% additional cost
            else:
                yield_increase = current_yield * 0.10   # 10% improvement
                additional_cost = current_cost * 0.08   # 8% additional cost
            
            revenue_increase = yield_increase * current_price
            net_profit_increase = revenue_increase - additional_cost
            
            yield_improvements[crop] = {
                "current_yield": current_yield,
                "improved_yield": current_yield + yield_increase,
                "yield_increase_percentage": (yield_increase / current_yield * 100) if current_yield > 0 else 0,
                "revenue_increase": revenue_increase,
                "additional_cost": additional_cost,
                "net_profit_increase": net_profit_increase
            }
            
            total_revenue_increase += revenue_increase
            total_implementation_cost += additional_cost
        
        scenario["changes"] = yield_improvements
        scenario["projected_profitability"] = {
            "total_revenue_increase": total_revenue_increase,
            "total_implementation_cost": total_implementation_cost,
            "net_profit_increase": total_revenue_increase - total_implementation_cost,
            "roi": ((total_revenue_increase - total_implementation_cost) / total_implementation_cost * 100) if total_implementation_cost > 0 else 0
        }
        scenario["implementation_cost"] = total_implementation_cost
        
        return scenario
    
    def _market_timing_optimization(self, crops: List[str], yields: Dict, prices: Dict, 
                                  costs: Dict, farm_size: float) -> Dict[str, Any]:
        """Optimize market timing for better prices"""
        scenario = {
            "name": "Market Timing Optimization",
            "description": "Optimize harvest and sale timing for better market prices",
            "changes": {},
            "projected_profitability": {},
            "implementation_cost": 0,
            "risk_level": "high"
        }
        
        market_optimizations = {}
        total_price_improvement = 0
        
        for crop in crops:
            current_yield = yields.get(crop, 0)
            current_price = prices.get(crop, 0)
            
            # Price improvement through better timing
            if crop in ["wheat", "maize"]:
                price_improvement = current_price * 0.12  # 12% price improvement
            elif crop in ["rice", "pulses"]:
                price_improvement = current_price * 0.08   # 8% price improvement
            else:
                price_improvement = current_price * 0.05   # 5% price improvement
            
            revenue_improvement = current_yield * price_improvement
            
            market_optimizations[crop] = {
                "current_price": current_price,
                "optimized_price": current_price + price_improvement,
                "price_improvement_percentage": (price_improvement / current_price * 100) if current_price > 0 else 0,
                "revenue_improvement": revenue_improvement,
                "storage_cost": revenue_improvement * 0.02,  # 2% storage cost
                "net_improvement": revenue_improvement - (revenue_improvement * 0.02)
            }
            
            total_price_improvement += market_optimizations[crop]["net_improvement"]
        
        scenario["changes"] = market_optimizations
        scenario["projected_profitability"] = {
            "total_price_improvement": total_price_improvement,
            "storage_costs": total_price_improvement * 0.02,
            "net_improvement": total_price_improvement,
            "improvement_percentage": 8  # Average improvement
        }
        scenario["implementation_cost"] = total_price_improvement * 0.05  # 5% implementation cost
        
        return scenario
    
    def _risk_adjusted_optimization(self, crops: List[str], yields: Dict, prices: Dict, 
                                  costs: Dict, farm_size: float, risk_tolerance: str) -> Dict[str, Any]:
        """Optimize for risk-adjusted returns"""
        scenario = {
            "name": "Risk-Adjusted Optimization",
            "description": "Balance profitability with risk management",
            "changes": {},
            "projected_profitability": {},
            "implementation_cost": 0,
            "risk_level": "low"
        }
        
        # Define risk factors for different crops
        crop_risk_factors = {
            "wheat": {"price_volatility": 0.15, "yield_volatility": 0.20, "risk_score": 0.18},
            "maize": {"price_volatility": 0.20, "yield_volatility": 0.25, "risk_score": 0.23},
            "rice": {"price_volatility": 0.12, "yield_volatility": 0.18, "risk_score": 0.15},
            "pulses": {"price_volatility": 0.18, "yield_volatility": 0.22, "risk_score": 0.20}
        }
        
        risk_adjusted_allocation = {}
        total_risk_adjusted_profit = 0
        
        for crop in crops:
            current_yield = yields.get(crop, 0)
            current_price = prices.get(crop, 0)
            current_cost = costs.get(crop, 0)
            current_profit = (current_yield * current_price) - current_cost
            
            risk_factors = crop_risk_factors.get(crop, {"risk_score": 0.20})
            risk_score = risk_factors["risk_score"]
            
            # Adjust allocation based on risk tolerance
            if risk_tolerance == "low":
                allocation_factor = max(0.1, 1 - risk_score)  # Reduce high-risk crops
            elif risk_tolerance == "high":
                allocation_factor = 1 + (risk_score * 0.5)    # Increase high-risk crops
            else:  # medium
                allocation_factor = 1.0
            
            adjusted_profit = current_profit * allocation_factor
            
            risk_adjusted_allocation[crop] = {
                "current_profit": current_profit,
                "risk_score": risk_score,
                "allocation_factor": allocation_factor,
                "adjusted_profit": adjusted_profit,
                "recommended_area_percentage": allocation_factor * 25  # 25% base allocation
            }
            
            total_risk_adjusted_profit += adjusted_profit
        
        scenario["changes"] = risk_adjusted_allocation
        scenario["projected_profitability"] = {
            "total_risk_adjusted_profit": total_risk_adjusted_profit,
            "risk_diversification_benefit": total_risk_adjusted_profit * 0.05,
            "overall_risk_score": sum(risk_adjusted_allocation[crop]["risk_score"] for crop in crops) / len(crops)
        }
        
        return scenario
    
    def _identify_best_strategies(self, scenarios: List[Dict], risk_tolerance: str) -> List[Dict[str, Any]]:
        """Identify the best strategies based on risk tolerance and profitability"""
        # Score each scenario
        scored_scenarios = []
        
        for scenario in scenarios:
            score = 0
            
            # Profitability score (40% weight)
            profit = scenario["projected_profitability"].get("total_profit", 0)
            if "net_profit_increase" in scenario["projected_profitability"]:
                profit = scenario["projected_profitability"]["net_profit_increase"]
            elif "net_improvement" in scenario["projected_profitability"]:
                profit = scenario["projected_profitability"]["net_improvement"]
            
            score += (profit / 1000) * 0.4  # Normalize to 0-1 scale
            
            # Risk score (30% weight)
            risk_level = scenario["risk_level"]
            risk_scores = {"low": 1.0, "medium": 0.7, "high": 0.4}
            score += risk_scores.get(risk_level, 0.7) * 0.3
            
            # Implementation feasibility (30% weight)
            implementation_cost = scenario["implementation_cost"]
            feasibility = max(0, 1 - (implementation_cost / 10000))  # Normalize to 0-1
            score += feasibility * 0.3
            
            scored_scenarios.append({
                "scenario": scenario,
                "score": score
            })
        
        # Sort by score and return top 3
        scored_scenarios.sort(key=lambda x: x["score"], reverse=True)
        return [item["scenario"] for item in scored_scenarios[:3]]
    
    def _generate_profit_recommendations(self, current_profitability: Dict, 
                                       best_strategies: List[Dict], 
                                       budget_constraints: Dict) -> List[str]:
        """Generate specific recommendations for profit improvement"""
        recommendations = []
        
        # Analyze current profitability
        current_margin = current_profitability.get("profit_margin", 0)
        current_roi = current_profitability.get("roi", 0)
        
        if current_margin < 20:
            recommendations.append("Focus on improving profit margins through cost optimization")
        
        if current_roi < 50:
            recommendations.append("Consider higher ROI crops or better resource allocation")
        
        # Strategy-specific recommendations
        for strategy in best_strategies:
            strategy_name = strategy["name"]
            if "Crop Mix" in strategy_name:
                recommendations.append("Reallocate farm area to more profitable crops")
            elif "Input Cost" in strategy_name:
                recommendations.append("Optimize input costs through better sourcing and application")
            elif "Yield Improvement" in strategy_name:
                recommendations.append("Invest in yield improvement through better management practices")
            elif "Market Timing" in strategy_name:
                recommendations.append("Improve market timing for better price realization")
            elif "Risk-Adjusted" in strategy_name:
                recommendations.append("Diversify crop portfolio for better risk management")
        
        # Budget-based recommendations
        available_budget = budget_constraints.get("available_budget", 0)
        if available_budget < 5000:
            recommendations.append("Focus on low-cost improvements like crop mix optimization")
        elif available_budget > 20000:
            recommendations.append("Consider major investments in yield improvement technologies")
        
        return recommendations
    
    def _analyze_risk_profiles(self, scenarios: List[Dict]) -> Dict[str, Any]:
        """Analyze risk profiles of different scenarios"""
        risk_analysis = {
            "low_risk_scenarios": [],
            "medium_risk_scenarios": [],
            "high_risk_scenarios": [],
            "risk_diversification_opportunities": []
        }
        
        for scenario in scenarios:
            risk_level = scenario["risk_level"]
            if risk_level == "low":
                risk_analysis["low_risk_scenarios"].append(scenario["name"])
            elif risk_level == "medium":
                risk_analysis["medium_risk_scenarios"].append(scenario["name"])
            else:
                risk_analysis["high_risk_scenarios"].append(scenario["name"])
        
        # Identify diversification opportunities
        if len(risk_analysis["low_risk_scenarios"]) > 0 and len(risk_analysis["high_risk_scenarios"]) > 0:
            risk_analysis["risk_diversification_opportunities"].append(
                "Combine low-risk cost optimization with high-risk yield improvement"
            )
        
        return risk_analysis
    
    def _analyze_budget_impact(self, best_strategies: List[Dict], budget_constraints: Dict) -> Dict[str, Any]:
        """Analyze budget impact of recommended strategies"""
        total_implementation_cost = sum(strategy["implementation_cost"] for strategy in best_strategies)
        available_budget = budget_constraints.get("available_budget", 0)
        
        return {
            "total_implementation_cost": total_implementation_cost,
            "available_budget": available_budget,
            "budget_deficit": max(0, total_implementation_cost - available_budget),
            "budget_surplus": max(0, available_budget - total_implementation_cost),
            "feasibility": "feasible" if total_implementation_cost <= available_budget else "requires_additional_funding",
            "prioritization": self._prioritize_strategies_by_budget(best_strategies, available_budget)
        }
    
    def _prioritize_strategies_by_budget(self, strategies: List[Dict], available_budget: float) -> List[str]:
        """Prioritize strategies based on available budget"""
        prioritized = []
        remaining_budget = available_budget
        
        # Sort strategies by cost-effectiveness (profit increase per dollar spent)
        cost_effective_strategies = []
        for strategy in strategies:
            implementation_cost = strategy["implementation_cost"]
            if implementation_cost > 0:
                profit_increase = strategy["projected_profitability"].get("total_profit", 0)
                if "net_profit_increase" in strategy["projected_profitability"]:
                    profit_increase = strategy["projected_profitability"]["net_profit_increase"]
                
                cost_effectiveness = profit_increase / implementation_cost
                cost_effective_strategies.append((strategy, cost_effectiveness))
        
        cost_effective_strategies.sort(key=lambda x: x[1], reverse=True)
        
        for strategy, cost_effectiveness in cost_effective_strategies:
            cost = strategy["implementation_cost"]
            if cost <= remaining_budget:
                prioritized.append(strategy["name"])
                remaining_budget -= cost
        
        return prioritized
