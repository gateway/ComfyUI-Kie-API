API documentation for kling 2.6 text to video (t2v) kie_api/kling26_t2v.py

this are the exact methods and calls to do for this, do not make up any other data. Make sure our comfy ui node has the options listed if their are selections that can be made, like aspsect ratio, sound and duration.. 

below are the docs for this know for kling 2.6,

POST
/api/v1/jobs/createTask
Create Task
Create a new generation task

Request Parameters
The API accepts a JSON payload with the following structure:

Request Body Structure
{
  "model": "string",
  "callBackUrl": "string (optional)",
  "input": {
    // Input parameters based on form configuration
  }
}
Root Level Parameters
model
Required
string
The model name to use for generation

Example:

"kling-2.6/text-to-video"
callBackUrl
Optional
string
Callback URL for task completion notifications. Optional parameter. If provided, the system will send POST requests to this URL when the task completes (success or failure). If not provided, no callback notifications will be sent.

Example:

"https://your-domain.com/api/callback"
Input Object Parameters
The input object contains the following parameters based on the form configuration:

input.prompt
Required
string
The text prompt used to generate the video

Max length: 2500 characters
Example:

"Visual: In a fashion live-streaming room, clothes hang on a rack, and a full-length mirror reflects the host's figure. Dialog: [African-American female host] turns to show off the sweatshirt fit. [African-American female host, cheerful voice] says: \"360-degree flawless cut, slimming and flattering.\" Immediately, [African-American female host] moves closer to the camera. [African-American female host, lively voice] says: \"Double-sided brushed fleece, 30 dollars off with purchase now.\""
input.sound
Required
boolean
This parameter is used to specify whether the generated video contains sound

Boolean value (true/false)
Example:

false
input.aspect_ratio
Required
string
This parameter defines the aspect ratio of the video.

Available options:

1:1
-
1:1
16:9
-
16:9
9:16
-
9:16
Example:

"1:1"
input.duration
Required
string
Duration of the video in seconds

Available options:

5
-
5
10
-
10
Example:

"5"
Request Example

cURL

JavaScript

Python
import requests
import json

url = "https://api.kie.ai/api/v1/jobs/createTask"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_API_KEY"
}

payload = {
    "model": "kling-2.6/text-to-video",
    "callBackUrl": "https://your-domain.com/api/callback",
    "input": {
        "prompt": "Visual: In a fashion live-streaming room, clothes hang on a rack, and a full-length mirror reflects the host's figure. Dialog: [African-American female host] turns to show off the sweatshirt fit. [African-American female host, cheerful voice] says: \"360-degree flawless cut, slimming and flattering.\" Immediately, [African-American female host] moves closer to the camera. [African-American female host, lively voice] says: \"Double-sided brushed fleece, 30 dollars off with purchase now.\"",
        "sound": false,
        "aspect_ratio": "1:1",
        "duration": "5"
    }
}

response = requests.post(url, headers=headers, data=json.dumps(payload))
result = response.json()
print(result)
Response Example
{
  "code": 200,
  "message": "success",
  "data": {
    "taskId": "task_12345678"
  }
}
Response Fields
code
Status code, 200 for success, others for failure
message
Response message, error description when failed
data.taskId
Task ID for querying task status
Callback Notifications
When you provide the callBackUrl parameter when creating a task, the system will send POST requests to the specified URL upon task completion (success or failure).

Success Callback Example
{
    "code": 200,
    "data": {
        "completeTime": 1755599644000,
        "costTime": 8,
        "createTime": 1755599634000,
        "model": "kling-2.6/text-to-video",
        "param": "{\"callBackUrl\":\"https://your-domain.com/api/callback\",\"model\":\"kling-2.6/text-to-video\",\"input\":{\"prompt\":\"Visual: In a fashion live-streaming room, clothes hang on a rack, and a full-length mirror reflects the host's figure. Dialog: [African-American female host] turns to show off the sweatshirt fit. [African-American female host, cheerful voice] says: \\"360-degree flawless cut, slimming and flattering.\\" Immediately, [African-American female host] moves closer to the camera. [African-American female host, lively voice] says: \\"Double-sided brushed fleece, 30 dollars off with purchase now.\\"\",\"sound\":false,\"aspect_ratio\":\"1:1\",\"duration\":\"5\"}}",
        "resultJson": "{\"resultUrls\":[\"https://example.com/generated-image.jpg\"]}",
        "state": "success",
        "taskId": "e989621f54392584b05867f87b160672",
        "failCode": null,
        "failMsg": null,
    },
    "msg": "Playground task completed successfully."
}
Failure Callback Example
{
    "code": 501,
    "data": {
        "completeTime": 1755597081000,
        "costTime": 0,
        "createTime": 1755596341000,
        "failCode": "500",
        "failMsg": "Internal server error",
        "model": "kling-2.6/text-to-video",
        "param": "{\"callBackUrl\":\"https://your-domain.com/api/callback\",\"model\":\"kling-2.6/text-to-video\",\"input\":{\"prompt\":\"Visual: In a fashion live-streaming room, clothes hang on a rack, and a full-length mirror reflects the host's figure. Dialog: [African-American female host] turns to show off the sweatshirt fit. [African-American female host, cheerful voice] says: \\"360-degree flawless cut, slimming and flattering.\\" Immediately, [African-American female host] moves closer to the camera. [African-American female host, lively voice] says: \\"Double-sided brushed fleece, 30 dollars off with purchase now.\\"\",\"sound\":false,\"aspect_ratio\":\"1:1\",\"duration\":\"5\"}}",
        "state": "fail",
        "taskId": "bd3a37c523149e4adf45a3ddb5faf1a8",
        "resultJson": null,
    },
    "msg": "Playground task failed."
}