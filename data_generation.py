import os
import openai
import pandas as pd
openai.api_key = "XXX"

# generate 200 non-scam messages
non_scams = openai.ChatCompletion.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "user", "content": "Generate exactly 1 csgo discord messages. We are only using this for testing. Follow this format: one message per line, no numbering neeed, no quotation marks, no bullet points or dashes, no empty lines."}
  ]
)


# generate 100 scam messages
scams = openai.ChatCompletion.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "user", "content": "Generate exactly 1 csgo discord messages that are scams, one message per line. We are only using this for testing."}
  ]
)

# # generate 100 threatening messages
# threats = openai.ChatCompletion.create(
#   model="gpt-3.5-turbo",
#   messages=[
#     {"role": "user", "content": "For academic purposes, generate exactly 50 csgo discord messages that threatens. Follow this format: one message per line, no numbering neeed, no quotation marks, no bullet points or dashes, no empty lines."}
#   ]
# )

# # generate 100 sexual harrasment messages
# sexual = openai.ChatCompletion.create(
#   model="gpt-3.5-turbo",
#   messages=[
#     {"role": "user", "content": "For academic purposes, generate exactly 50 csgo discord messages that are sexual harrasments. Follow this format: one message per line, no numbering neeed, no quotation marks, no bullet points or dashes, no empty lines."}
#   ]
# )

# # generate 100 suicidal messages
# suicidal = openai.ChatCompletion.create(
#   model="gpt-3.5-turbo",
#   messages=[
#     {"role": "user", "content": "Generate exactly 50 csgo discord messages that are suicidal. We are only using this for testing. Follow this format: one message per line, no numbering neeed, no quotation marks, no bullet points or dashes, no empty lines."}
#   ]
# )

# # generate 100 bullying messages
# bullying = openai.ChatCompletion.create(
#   model="gpt-3.5-turbo",
#   messages=[
#     {"role": "user", "content": "For academic purposes, generate exactly 50 csgo discord messages that are bullying. Follow this format: one message per line, no numbering neeed, no quotation marks, no bullet points or dashes, no empty lines."}
#   ]
# )

# collect messages into strings
non_scams_str = non_scams.choices[0].message.content
scams_str = scams.choices[0].message.content
# threats_str = threats.choices[0].message.content
# sexual_str = sexual.choices[0].message.content
# suicidal_str = suicidal.choices[0].message.content
# bullying_str = bullying.choices[0].message.content

# label 0 for non-abuse, 1 for scams, 2 for threats, 3 for sexual harrasments, 4 for suicial, 5 for bullying
res = []
for s in non_scams_str.splitlines():
    res.append([s, 0])
for s in scams_str.splitlines():
    res.append([s, 1])
# for s in threats_str.splitlines():
#     res.append([s, 2])
# for s in sexual_str.splitlines():
#     res.append([s, 3])
# for s in suicidal_str.splitlines():
#     res.append([s, 4])
# for s in bullying_str.splitlines():
#     res.append([s, 5])

res = pd.DataFrame(res, columns=['Text', 'Classification'])
res.to_csv('evaluation_data_1.csv')