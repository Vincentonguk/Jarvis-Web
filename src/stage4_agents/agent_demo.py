import argparse
import logging
import os
from typing import Iterable, List, Optional

LOGGER = logging.getLogger(__name__)


class Memory:
    """Lightweight in-memory log to mimic short-term recall for the agent."""

    def __init__(self) -> None:
        self.events: List[str] = []

    def remember(self, entry: str) -> None:
        self.events.append(entry)

    def recall(self) -> List[str]:
        return list(self.events)

    def recent(self, limit: Optional[int] = None) -> List[str]:
        """Return the most recent events, preserving order."""
        if limit is None:
            return self.recall()
        return list(self.events[-limit:])


class ToolRegistry:
    """Registry of mock tools the Worker can call to act on the environment."""

    def __init__(self) -> None:
        self.tools = {
            "data_extractor": "Fetched customer churn dataset",
            "model_trainer": "Trained gradient boosting model",
            "evaluation_suite": "Calculated ROC-AUC and precision-recall curves",
            "deployment_pipeline": "Shipped model to production with feature monitoring",
        }

    def list_tools(self) -> List[str]:
        return list(self.tools.keys())

    def use(self, name: Optional[str]) -> str:
        if name is None:
            return "Executed step with no external tool"
        return self.tools.get(name, f"Tool '{name}' not found")


class Planner:
    def plan(self, goal: str) -> List[str]:
        """Return a transparent, tool-annotated plan."""
        return [
            f"Analyze goal: {goal}",
            "Collect relevant data [tool:data_extractor]",
            "Train baseline model [tool:model_trainer]",
            "Evaluate results [tool:evaluation_suite]",
            "Deploy system [tool:deployment_pipeline]",
            "Confirm monitoring thresholds and alerting",
        ]


class Worker:
    def execute(self, steps: Iterable[str], tools: ToolRegistry, memory: Memory) -> List[str]:
        results: List[str] = []
        for idx, step in enumerate(steps, start=1):
            tool_used: Optional[str] = None
            if "[tool:" in step:
                tool_used = step.split("[tool:")[1].split("]")[0].strip()

            action_result = tools.use(tool_used)
            record = f"Step {idx}: {step} -> {action_result}"

            memory.remember(record)
            results.append(record)

        return results


class Critic:
    def review(self, results: Iterable[str], memory: Memory) -> List[str]:
        feedback: List[str] = []
        result_list = list(results)

        for r in result_list:
            if "Deploy system" in r or "Deploy" in r:
                feedback.append("Add monitoring, logging, and rollback strategy")

        if not feedback:
            feedback.append("Execution looks safe, but continuous validation is required")

        if len(memory.recall()) < len(result_list):
            feedback.append("Memory is missing some steps—verify logging pipeline")
        elif not memory.recent(1):
            feedback.append("No execution events captured in memory")
        else:
            last_event = memory.recent(1)[0]
            step_label = last_event.split(":")[0]
            feedback.append(f"Last recorded event: {step_label} (details redacted)")

        return feedback


def configure_logging(verbose: Optional[bool] = None) -> None:
    if verbose is None:
        env_value = os.getenv("AGENT_DEMO_VERBOSE") or os.getenv("DEBUG")
        verbose = env_value == "1" or (env_value or "").lower() in {"true", "yes", "on"}

    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s", force=True)
    LOGGER.debug("Logger configured with verbose=%s", verbose)


def run_stage4_demo(verbose: Optional[bool] = None) -> None:
    configure_logging(verbose)

    goal = "Build a production-ready churn prediction system"

    planner = Planner()
    worker = Worker()
    critic = Critic()
    memory = Memory()
    tools = ToolRegistry()

    plan = planner.plan(goal)
    results = worker.execute(plan, tools=tools, memory=memory)
    feedback = critic.review(results, memory=memory)

    LOGGER.info("[Stage 4] Agentic & Multi-Agent System Demo")
    LOGGER.info("Goal: %s", goal)
    LOGGER.info("Plan steps: %d", len(plan))
    LOGGER.info("Execution steps: %d", len(results))
    LOGGER.info("Memory captured %d events", len(memory.recall()))
    LOGGER.info("Critic feedback items: %d", len(feedback))

    LOGGER.debug("Tools available: %s", ", ".join(tools.list_tools()))

    if logging.getLogger().isEnabledFor(logging.DEBUG):
        print("\nGOAL:", goal)
        print("\n--- PLAN ---")
        for step in plan:
            print("-", step)

        print("\n--- EXECUTION ---")
        for r in results:
            print("-", r)

        print("\n--- CRITIC FEEDBACK ---")
        for f in feedback:
            print("-", f)

        print("\nStage 4 Complete.\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the stage 4 agent demo")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    run_stage4_demo(verbose=args.verbose)


if __name__ == "__main__":
    main()
