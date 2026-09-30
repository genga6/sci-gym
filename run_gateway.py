"""Run a SciGym task with any model served by Vercel AI Gateway.

Usage:
    uv run python run_gateway.py --model anthropic/claude-sonnet-4.5
    uv run python run_gateway.py --model openai/gpt-5 --task BIOMD0000000029
"""

import argparse
import os
import tempfile

import yaml
from dotenv import load_dotenv
from openai import OpenAI

from scigym.agent import GPT
from scigym.main import setup_controller

load_dotenv()

GATEWAY_BASE_URL = "https://ai-gateway.vercel.sh/v1"


class Gateway(GPT):
    """SciGym agent talking to Vercel AI Gateway's OpenAI-compatible API.

    Model names use the gateway's `provider/model` form, e.g.
    `anthropic/claude-sonnet-4.5`, `openai/gpt-5`, `google/gemini-2.5-pro`.
    """

    def initialize(self):
        self.client = OpenAI(api_key=self.api_key, base_url=GATEWAY_BASE_URL)
        self.messages = []
        if self.system_prompt:
            self.messages.append({"role": "system", "content": self.system_prompt})


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", required=True, help="gateway model id, e.g. anthropic/claude-sonnet-4.5")
    parser.add_argument("--config", default="configs/small.yml")
    parser.add_argument("--task", help="override benchmark_dir with data/small/<TASK>")
    args = parser.parse_args()

    api_key = os.getenv("VERCEL_AI_GATEWAY_API_KEY")
    if not api_key:
        raise SystemExit("VERCEL_AI_GATEWAY_API_KEY is not set (Codespaces secret or .env)")

    config_path = args.config
    if args.task:
        with open(config_path) as f:
            config = yaml.safe_load(f)
        config["benchmark_dir"] = os.path.join("data", "small", args.task)
        tmp = tempfile.NamedTemporaryFile("w", suffix=".yml", delete=False)
        yaml.safe_dump(config, tmp)
        tmp.close()
        config_path = tmp.name

    controller = setup_controller(config_path, args.model)
    llm = Gateway(
        model_name=args.model,
        api_key=api_key,
        system_prompt=controller._create_system_prompt(),
        temperature=controller.temperature,
    )
    controller.run_benchmark(model=llm)


if __name__ == "__main__":
    main()
