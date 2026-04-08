#!/bin/bash
docker build -t sovereignty-ai-studio .
docker run -it --rm sovereignty-ai-studio python ai_core/second_squad_agent.py