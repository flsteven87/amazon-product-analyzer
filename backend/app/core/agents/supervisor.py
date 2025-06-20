"""Supervisor Agent for coordinating the multi-agent workflow."""

from typing import Dict, Any, List

from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

from app.core.agents.base import BaseAgent
from app.core.graph.state import AnalysisState


class SupervisorAgent(BaseAgent):
    """Supervisor agent that coordinates other agents and manages workflow."""

    def __init__(self, llm: ChatOpenAI):
        """Initialize the Supervisor Agent.

        Args:
            llm: The language model instance
        """
        super().__init__(llm, "SupervisorAgent")
        self.agents = ["data_collector", "market_analyzer", "optimization_advisor", "FINISH"]

    def execute(self, state: AnalysisState) -> AnalysisState:
        """Decide which agent should act next based on workflow analysis."""
        try:
            # Check iteration count
            iteration = state.get("iteration_count", 0) + 1
            state["iteration_count"] = iteration

            self.logger.info(f"SupervisorAgent iteration {iteration}")

            max_iterations = state.get("max_iterations", 10)
            if iteration >= max_iterations:
                self.logger.info(f"Reached max iterations ({max_iterations}), finishing workflow")
                state["next_agent"] = "FINISH"
                return state

            # Analyze current workflow state
            workflow_status = self._analyze_workflow_status(state)
            self.logger.info(f"Workflow status: {workflow_status}")

            # Determine next agent using logic + LLM validation
            next_agent = self._determine_next_agent(state, workflow_status)

            # Validate with LLM for complex scenarios
            if self._should_validate_with_llm(workflow_status):
                next_agent = self._validate_with_llm(state, next_agent, workflow_status)

            state["next_agent"] = next_agent

            # Add supervisor message
            status_msg = f"Supervisor: Next agent is {next_agent} (iteration {iteration})"
            if workflow_status.get("errors"):
                status_msg += f" - Errors detected: {len(workflow_status['errors'])}"

            state["messages"].append(AIMessage(content=status_msg))

            self.logger.info(f"SupervisorAgent selected next agent: {next_agent}")
            return state

        except Exception as e:
            self.logger.error(f"SupervisorAgent error: {str(e)}", exc_info=True)
            # Emergency fallback
            state["next_agent"] = "FINISH"
            state["messages"].append(AIMessage(content=f"Supervisor: Error occurred, terminating workflow: {str(e)}"))
            return state

    def _analyze_workflow_status(self, state: AnalysisState) -> Dict[str, Any]:
        """Analyze current workflow status and detect issues."""
        status = {
            "product_data_collected": False,
            "competitor_data_collected": False,
            "market_analysis_completed": False,
            "optimization_completed": False,
            "data_source": None,
            "errors": [],
            "warnings": [],
            "competitor_count": 0,
        }

        # Check product data
        product_data = state.get("product_data", {})
        if product_data.get("status") == "collected":
            status["product_data_collected"] = True
            status["data_source"] = product_data.get("source", "unknown")

            # Check data quality
            if status["data_source"] == "llm_fallback":
                status["warnings"].append("Using LLM fallback instead of real scraping")
            elif not product_data.get("scraped_data") and not product_data.get("structured_analysis"):
                status["warnings"].append("Product data may be incomplete")

        # Check competitor data collection - CHECK IN REAL TIME
        competitor_data = state.get("competitor_data", [])
        competitor_candidates = state.get("competitor_candidates", [])

        if competitor_data:
            status["competitor_data_collected"] = True
            status["competitor_count"] = len(competitor_data)
            status["competitor_data_source"] = "detailed"
            self.logger.info(f"Status: Using {len(competitor_data)} detailed competitors for analysis")
        elif competitor_candidates:
            # Use candidate data for analysis - no need for detailed collection
            status["competitor_data_collected"] = True
            status["competitor_count"] = len(competitor_candidates)
            status["competitor_data_source"] = "candidates"
            self.logger.info(f"Status: Using {len(competitor_candidates)} competitor candidates for analysis")
        else:
            # Check if we're still in data collection phase (no competitors discovered yet)
            if not status["product_data_collected"]:
                # Still collecting main product data, competitors not discovered yet
                status["competitor_data_collected"] = False
                status["competitor_count"] = 0
                status["competitor_data_source"] = "pending"
                self.logger.info("Status: Competitor discovery pending - main product collection not complete")
            else:
                # Product data collected but no competitors found
                status["competitor_data_collected"] = True
                status["competitor_count"] = 0
                status["competitor_data_source"] = "none"
                status["warnings"].append("No competitor candidates discovered during data collection")
                self.logger.info("Status: No competitors discovered during data collection")

        # Check market analysis
        market_analysis = state.get("market_analysis", {})
        if market_analysis.get("status") == "completed":
            status["market_analysis_completed"] = True
            if not market_analysis.get("analysis"):
                status["warnings"].append("Market analysis appears empty")

        # Check optimization advice
        optimization = state.get("optimization_advice", {})
        if optimization.get("status") == "completed":
            status["optimization_completed"] = True
            if not optimization.get("recommendations"):
                status["warnings"].append("Optimization advice appears empty")

        return status

    def _determine_next_agent(self, state: AnalysisState, workflow_status: Dict[str, Any]) -> str:
        """Determine next agent using enhanced business logic with competitor analysis."""
        # Simplified workflow - use competitor candidates directly for analysis
        # Phase 1: Main product data collection (includes competitor discovery)
        if not workflow_status["product_data_collected"]:
            state["analysis_phase"] = "main_product"
            return "data_collector"

        # Phase 2: Market analysis (with available competitor data)
        elif workflow_status["product_data_collected"] and not workflow_status["market_analysis_completed"]:
            # Determine analysis type based on available competitor data
            competitor_count = workflow_status.get("competitor_count", 0)
            if competitor_count > 0:
                self.logger.info(f"Proceeding to competitive analysis with {competitor_count} competitors")
                state["analysis_phase"] = "competitive_analysis"
            else:
                self.logger.info("No competitors available, proceeding to basic market analysis")
                state["analysis_phase"] = "basic_analysis"
            return "market_analyzer"

        # Phase 3: Optimization recommendations (based on market analysis)
        elif workflow_status["market_analysis_completed"] and not workflow_status["optimization_completed"]:
            state["analysis_phase"] = "optimization"
            return "optimization_advisor"

        # NEW Phase 4: Report synthesis and quality enhancement
        elif (workflow_status["product_data_collected"] and 
              workflow_status["market_analysis_completed"] and 
              workflow_status["optimization_completed"] and
              state.get("analysis_phase") != "report_synthesis"):
            return self._perform_report_synthesis(state)

        # All phases complete including synthesis
        else:
            return "FINISH"

    def _should_validate_with_llm(self, workflow_status: Dict[str, Any]) -> bool:
        """Determine if LLM validation is needed for complex scenarios."""
        # Use LLM validation if there are warnings or complex situations
        return bool(workflow_status.get("warnings") or workflow_status.get("errors"))

    def _validate_with_llm(self, state: AnalysisState, suggested_agent: str, workflow_status: Dict[str, Any]) -> str:
        """Use LLM to validate agent selection in complex scenarios."""
        try:
            # Create a prompt for complex decision making
            messages_summary = "\n".join([f"{msg.type}: {msg.content[:150]}..." for msg in state["messages"][-3:]])

            prompt = f"""You are a supervisor managing a product analysis workflow. 
            
            Current Status:
            - Product Data: {"✅ Collected" if workflow_status["product_data_collected"] else "❌ Not collected"} (Source: {workflow_status.get("data_source", "N/A")})
            - Market Analysis: {"✅ Completed" if workflow_status["market_analysis_completed"] else "❌ Not completed"}
            - Optimization: {"✅ Completed" if workflow_status["optimization_completed"] else "❌ Not completed"}
            
            Warnings: {", ".join(workflow_status.get("warnings", ["None"]))}
            Errors: {", ".join(workflow_status.get("errors", ["None"]))}
            
            Suggested next agent: {suggested_agent}
            
            Recent messages:
            {messages_summary}
            
            Available agents: data_collector, market_analyzer, optimization_advisor, FINISH
            
            Should we proceed with '{suggested_agent}' or choose a different agent? Consider:
            - Data quality issues may require re-collection
            - Missing analysis may need retry
            - All tasks complete means FINISH
            
            Respond with ONLY the agent name."""

            response = self.llm.invoke([HumanMessage(content=prompt)])
            llm_choice = response.content.strip().lower().replace(" ", "_")

            # Validate LLM choice
            if llm_choice in [a.lower() for a in self.agents]:
                if llm_choice != suggested_agent.lower():
                    self.logger.info(f"LLM overrode suggestion: {suggested_agent} -> {llm_choice}")
                return llm_choice
            else:
                self.logger.warning(f"LLM returned invalid choice '{llm_choice}', using original suggestion")
                return suggested_agent

        except Exception as e:
            self.logger.error(f"LLM validation failed: {str(e)}")
            return suggested_agent

    def _perform_report_synthesis(self, state: AnalysisState) -> str:
        """執行報告綜合處理，提升報告質量和一致性。"""
        try:
            self.logger.info("Starting report synthesis phase")
            state["analysis_phase"] = "report_synthesis"
            
            # Step 1: 質量評估
            quality_score = self._assess_report_quality(state)
            self.logger.info(f"Report quality score: {quality_score:.2f}/1.0")
            
            # Step 2: 內容綜合處理
            synthesized_content = self._synthesize_agent_outputs(state)
            
            # Step 3: 通用內容過濾
            final_content = self._remove_generic_content(synthesized_content)
            
            # Step 4: 更新state中的各部分內容
            self._update_synthesized_content(state, final_content)
            
            # 添加synthesis消息
            status_msg = f"Supervisor: Report synthesis completed (quality score: {quality_score:.2f})"
            state["messages"].append(AIMessage(content=status_msg))
            
            self.logger.info("Report synthesis phase completed")
            
            # Synthesis完成後，返回FINISH
            return "FINISH"
            
        except Exception as e:
            self.logger.error(f"Report synthesis failed: {str(e)}", exc_info=True)
            # 如果synthesis失敗，直接finish
            return "FINISH"

    def _assess_report_quality(self, state: AnalysisState) -> float:
        """評估報告質量分數（0.0-1.0）。"""
        score = 0.0
        
        # 檢查產品數據質量 (0.3分) - 使用新的validation metrics
        product_data = state.get("product_data", {})
        if product_data.get("source") == "scraper":
            # Use detailed quality metrics if available
            if "quality_score" in product_data:
                score += 0.2 + (product_data["quality_score"] * 0.1)  # Base 0.2 + up to 0.1 bonus
            else:
                score += 0.3
            
            # Additional bonus for data completeness
            if "data_completeness" in product_data:
                completeness_score = product_data["data_completeness"]["overall_score"]
                score += completeness_score * 0.05  # Up to 0.05 bonus
                
        elif product_data.get("source") == "llm_fallback":
            score += 0.1
            
        # 檢查競爭對手數據 (0.2分)
        competitor_data = state.get("competitor_data", [])
        competitor_candidates = state.get("competitor_candidates", [])
        if competitor_data:
            score += 0.2
        elif competitor_candidates:
            # Score based on number of competitors found
            competitor_count = len(competitor_candidates)
            if competitor_count >= 5:
                score += 0.15
            elif competitor_count >= 2:
                score += 0.1
            else:
                score += 0.05
            
        # 檢查市場分析內容質量 (0.3分)
        market_analysis = state.get("market_analysis", {})
        analysis_content = market_analysis.get("analysis", "")
        if len(analysis_content) > 500 and any(keyword in analysis_content.lower() for keyword in ["specific", "asin", "competitor", "price"]):
            score += 0.3
        elif len(analysis_content) > 200:
            score += 0.2
        elif analysis_content:
            score += 0.1
            
        # 檢查優化建議內容質量 (0.2分)
        optimization = state.get("optimization_advice", {})
        recommendations = optimization.get("recommendations", "")
        if len(recommendations) > 300 and any(keyword in recommendations.lower() for keyword in ["recommend", "improve", "optimize", "strategy"]):
            score += 0.2
        elif len(recommendations) > 100:
            score += 0.1
            
        return min(score, 1.0)

    def _synthesize_agent_outputs(self, state: AnalysisState) -> Dict[str, str]:
        """使用LLM重新綜合各agent輸出，提升內容連貫性。"""
        try:
            # 提取各agent的原始輸出
            product_data = state.get("product_data", {})
            market_analysis = state.get("market_analysis", {})
            optimization_advice = state.get("optimization_advice", {})
            
            # 獲取產品和競爭對手信息
            asin = state.get("asin", "Unknown")
            competitor_info = self._get_competitor_summary(state)
            
            # 構建LLM prompt進行內容重新綜合
            prompt = f"""You are a professional product analysis report editor. Based on the following original analysis content, reorganize and rewrite to generate more coherent, specific, and valuable analysis reports.

**Product ASIN**: {asin}

**Original Product Data**:
{self._extract_content_for_synthesis(product_data)}

**Original Market Analysis**:
{market_analysis.get('analysis', 'No analysis available')}

**Original Optimization Recommendations**:
{optimization_advice.get('recommendations', 'No recommendations available')}

**Competitor Information**:
{competitor_info}

Please reorganize the above content with the following requirements:
1. Remove any template-style or generic descriptions
2. Integrate information and avoid repetition
3. Ensure logical coherence and consistency
4. Provide specific insights based on actual data
5. If specific data is lacking, clearly state the limitations

Please provide separately:
1. **Reorganized Product Overview**
2. **Reorganized Market Analysis** 
3. **Reorganized Optimization Recommendations**

Format requirement: Each section should start with "### [Section Name]"."""

            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content
            
            # 解析LLM回應，分離各個部分
            return self._parse_synthesized_content(content)
            
        except Exception as e:
            self.logger.error(f"Content synthesis failed: {str(e)}")
            # 返回原始內容
            return {
                "product_overview": self._extract_content_for_synthesis(product_data),
                "market_analysis": market_analysis.get("analysis", ""),
                "optimization_recommendations": optimization_advice.get("recommendations", "")
            }

    def _get_competitor_summary(self, state: AnalysisState) -> str:
        """獲取競爭對手信息摘要。"""
        competitor_data = state.get("competitor_data", [])
        competitor_candidates = state.get("competitor_candidates", [])
        
        if competitor_data:
            return f"Found {len(competitor_data)} detailed competitor data entries"
        elif competitor_candidates:
            return f"Found {len(competitor_candidates)} competitor candidates"
        else:
            return "No competitor data discovered"

    def _extract_content_for_synthesis(self, product_data: dict) -> str:
        """提取產品數據內容用於綜合。"""
        if product_data.get("structured_analysis"):
            return product_data["structured_analysis"]
        elif product_data.get("llm_analysis"):
            return product_data["llm_analysis"]
        elif product_data.get("raw_analysis"):
            return product_data["raw_analysis"]
        else:
            return "No product data available"

    def _parse_synthesized_content(self, content: str) -> Dict[str, str]:
        """解析LLM綜合後的內容。"""
        result = {
            "product_overview": "",
            "market_analysis": "",
            "optimization_recommendations": ""
        }
        
        # 分割內容
        sections = content.split("###")
        
        for section in sections:
            section = section.strip()
            if "Product Overview" in section:
                result["product_overview"] = section.replace("Product Overview", "").strip()
            elif "Market Analysis" in section:
                result["market_analysis"] = section.replace("Market Analysis", "").strip()
            elif "Optimization" in section:
                result["optimization_recommendations"] = section.replace("Optimization Recommendations", "").replace("Optimization", "").strip()
        
        return result

    def _remove_generic_content(self, synthesized_content: Dict[str, str]) -> Dict[str, str]:
        """移除通用和模板式內容。"""
        generic_phrases = [
            "I'm unable to access external URLs",
            "However, I can guide you",
            "Here's a structured analysis template",
            "Feel free to use this template",
            "based on the URL you provided",
            "template you can use to fill in",
            "This could be based on",
            "For example, if",
            "might look for"
        ]
        
        filtered_content = {}
        
        for key, content in synthesized_content.items():
            # 移除包含通用短語的段落
            filtered_lines = []
            for line in content.split('\n'):
                if not any(phrase in line for phrase in generic_phrases):
                    filtered_lines.append(line)
            
            filtered_content[key] = '\n'.join(filtered_lines).strip()
        
        return filtered_content

    def _update_synthesized_content(self, state: AnalysisState, synthesized_content: Dict[str, str]):
        """更新state中的內容為綜合後的版本。"""
        # 更新產品數據
        if "product_overview" in synthesized_content and synthesized_content["product_overview"]:
            product_data = state.get("product_data", {})
            product_data["synthesized_analysis"] = synthesized_content["product_overview"]
            state["product_data"] = product_data
            
        # 更新市場分析
        if "market_analysis" in synthesized_content and synthesized_content["market_analysis"]:
            market_analysis = state.get("market_analysis", {})
            market_analysis["synthesized_analysis"] = synthesized_content["market_analysis"]
            state["market_analysis"] = market_analysis
            
        # 更新優化建議
        if "optimization_recommendations" in synthesized_content and synthesized_content["optimization_recommendations"]:
            optimization_advice = state.get("optimization_advice", {})
            optimization_advice["synthesized_recommendations"] = synthesized_content["optimization_recommendations"]
            state["optimization_advice"] = optimization_advice
