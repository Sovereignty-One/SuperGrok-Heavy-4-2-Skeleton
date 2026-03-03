# agents:
#   - id: researcher
#     role: Research Assistant
#     goal: Find key insights about electric vehicles
#     tools:
#       - python
# 
#   - id: writer
#     role: Content Writer
#     goal: Write a concise summary using the research
# 
# workflow:
#   type: sequential
#   steps:
#     - agent: researcher
#     - agent: writer