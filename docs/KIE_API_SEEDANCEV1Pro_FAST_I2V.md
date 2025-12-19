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

"bytedance/v1-pro-fast-image-to-video"
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

Max length: 10000 characters
Example:

"A cinematic close-up sequence of a single elegant ceramic coffee cup with saucer on a rustic wooden table near a sunlit window, hot rich espresso poured in a thin golden stream from above, gradually filling the cup in distinct stages: empty with faint steam, 1/4 filled with dark crema, half-filled with swirling coffee and rising steam, 3/4 filled nearing the rim, perfectly full just below overflow with glossy surface and soft bokeh highlights; ultra-realistic, warm golden-hour light, shallow depth of field, photorealism, detailed textures, subtle steam wisps, serene inviting atmosphere --ar 16:9 --q 2 --style raw"
input.image_url
Required
string(URL)
The URL of the image used to generate video

File URL after upload, not file content; Accepted types: image/jpeg, image/png, image/webp; Max size: 10.0MB
Example:

"https://file.aiquickdraw.com/custom-page/akr/section-images/1762340693669m6sey187.webp"
input.resolution
Optional
string
Video resolution - 480p for faster generation, 720p for balance, 1080p for higher quality

Available options:

720p
-
720p
1080p
-
1080p
Example:

"720p"
input.duration
Optional
string
Duration of the video in seconds

Available options:

5
-
5s
10
-
10s
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
    "model": "bytedance/v1-pro-fast-image-to-video",
    "callBackUrl": "https://your-domain.com/api/callback",
    "input": {
        "prompt": "A cinematic close-up sequence of a single elegant ceramic coffee cup with saucer on a rustic wooden table near a sunlit window, hot rich espresso poured in a thin golden stream from above, gradually filling the cup in distinct stages: empty with faint steam, 1/4 filled with dark crema, half-filled with swirling coffee and rising steam, 3/4 filled nearing the rim, perfectly full just below overflow with glossy surface and soft bokeh highlights; ultra-realistic, warm golden-hour light, shallow depth of field, photorealism, detailed textures, subtle steam wisps, serene inviting atmosphere --ar 16:9 --q 2 --style raw",
        "image_url": "https://file.aiquickdraw.com/custom-page/akr/section-images/1762340693669m6sey187.webp",
        "resolution": "720p",
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
        "model": "bytedance/v1-pro-fast-image-to-video",
        "param": "{\"callBackUrl\":\"https://your-domain.com/api/callback\",\"model\":\"bytedance/v1-pro-fast-image-to-video\",\"input\":{\"prompt\":\"A cinematic close-up sequence of a single elegant ceramic coffee cup with saucer on a rustic wooden table near a sunlit window, hot rich espresso poured in a thin golden stream from above, gradually filling the cup in distinct stages: empty with faint steam, 1/4 filled with dark crema, half-filled with swirling coffee and rising steam, 3/4 filled nearing the rim, perfectly full just below overflow with glossy surface and soft bokeh highlights; ultra-realistic, warm golden-hour light, shallow depth of field, photorealism, detailed textures, subtle steam wisps, serene inviting atmosphere --ar 16:9 --q 2 --style raw\",\"image_url\":\"https://file.aiquickdraw.com/custom-page/akr/section-images/1762340693669m6sey187.webp\",\"resolution\":\"720p\",\"duration\":\"5\"}}",
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
        "model": "bytedance/v1-pro-fast-image-to-video",
        "param": "{\"callBackUrl\":\"https://your-domain.com/api/callback\",\"model\":\"bytedance/v1-pro-fast-image-to-video\",\"input\":{\"prompt\":\"A cinematic close-up sequence of a single elegant ceramic coffee cup with saucer on a rustic wooden table near a sunlit window, hot rich espresso poured in a thin golden stream from above, gradually filling the cup in distinct stages: empty with faint steam, 1/4 filled with dark crema, half-filled with swirling coffee and rising steam, 3/4 filled nearing the rim, perfectly full just below overflow with glossy surface and soft bokeh highlights; ultra-realistic, warm golden-hour light, shallow depth of field, photorealism, detailed textures, subtle steam wisps, serene inviting atmosphere --ar 16:9 --q 2 --style raw\",\"image_url\":\"https://file.aiquickdraw.com/custom-page/akr/section-images/1762340693669m6sey187.webp\",\"resolution\":\"720p\",\"duration\":\"5\"}}",
        "remainedCredits": 2510430,
        "state": "fail",
        "taskId": "bd3a37c523149e4adf45a3ddb5faf1a8",
        "updateTime": 1755597097000
    },
    "msg": "Playground task failed."
}