spec to create a new node for kling , this is a video mode... which is image to text.

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

"kling-2.6/image-to-video"
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

Max length: 1000 characters
Example:

"In a bright rehearsal room, sunlight streams through the window, and a standing microphone is placed in the center of the room. [Campus band female lead singer] stands in front of the microphone with her eyes closed, while the other members stand around her. [Campus band female lead singer, full voice] leads: \"I will try to fix you, with all my heart and soul...\" The background is an a cappella harmony, and the camera slowly circles around the band members."
input.image_urls
Required
array(URL)
The URL of the image used to generate video

File URL after upload, not file content; Accepted types: image/jpeg, image/png, image/webp; Max size: 10.0MB
Example:

["https://static.aiquickdraw.com/tools/example/1764851002741_i0lEiI8I.png"]
input.sound
Required
boolean
This parameter is used to specify whether the generated video contains sound

Boolean value (true/false)
Example:

false
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
    "model": "kling-2.6/image-to-video",
    "callBackUrl": "https://your-domain.com/api/callback",
    "input": {
        "prompt": "In a bright rehearsal room, sunlight streams through the window, and a standing microphone is placed in the center of the room. [Campus band female lead singer] stands in front of the microphone with her eyes closed, while the other members stand around her. [Campus band female lead singer, full voice] leads: \"I will try to fix you, with all my heart and soul...\" The background is an a cappella harmony, and the camera slowly circles around the band members.",
        "image_urls": [
            "https://static.aiquickdraw.com/tools/example/1764851002741_i0lEiI8I.png"
        ],
        "sound": false,
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
        "consumeCredits": 100,
        "costTime": 8,
        "createTime": 1755599634000,
        "model": "kling-2.6/image-to-video",
        "param": "{\"callBackUrl\":\"https://your-domain.com/api/callback\",\"model\":\"kling-2.6/image-to-video\",\"input\":{\"prompt\":\"In a bright rehearsal room, sunlight streams through the window, and a standing microphone is placed in the center of the room. [Campus band female lead singer] stands in front of the microphone with her eyes closed, while the other members stand around her. [Campus band female lead singer, full voice] leads: \\"I will try to fix you, with all my heart and soul...\\" The background is an a cappella harmony, and the camera slowly circles around the band members.\",\"image_urls\":[\"https://static.aiquickdraw.com/tools/example/1764851002741_i0lEiI8I.png\"],\"sound\":false,\"duration\":\"5\"}}",
        "remainedCredits": 2510330,
        "resultJson": "{\"resultUrls\":[\"https://example.com/generated-image.jpg\"]}",
        "state": "success",
        "taskId": "e989621f54392584b05867f87b160672",
        "updateTime": 1755599644000
    },
    "msg": "Playground task completed successfully."
}
Failure Callback Example
{
    "code": 501,
    "data": {
        "completeTime": 1755597081000,
        "consumeCredits": 0,
        "costTime": 0,
        "createTime": 1755596341000,
        "failCode": "500",
        "failMsg": "Internal server error",
        "model": "kling-2.6/image-to-video",
        "param": "{\"callBackUrl\":\"https://your-domain.com/api/callback\",\"model\":\"kling-2.6/image-to-video\",\"input\":{\"prompt\":\"In a bright rehearsal room, sunlight streams through the window, and a standing microphone is placed in the center of the room. [Campus band female lead singer] stands in front of the microphone with her eyes closed, while the other members stand around her. [Campus band female lead singer, full voice] leads: \\"I will try to fix you, with all my heart and soul...\\" The background is an a cappella harmony, and the camera slowly circles around the band members.\",\"image_urls\":[\"https://static.aiquickdraw.com/tools/example/1764851002741_i0lEiI8I.png\"],\"sound\":false,\"duration\":\"5\"}}",
        "remainedCredits": 2510430,
        "state": "fail",
        "taskId": "bd3a37c523149e4adf45a3ddb5faf1a8",
        "updateTime": 1755597097000
    },
    "msg": "Playground task failed."
}