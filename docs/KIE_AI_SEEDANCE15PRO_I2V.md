Seedance 1.5 Pro I2V api call for Kie.

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

"bytedance/seedance-1.5-pro"
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
Enter video description (3-2500 characters)...

Max length: 2500 characters
Example:

"In a Chinese-English communication scenario, a 70-year-old old man said kindly to the child: Good boy, study hard where you are in China ! The child happily replied in Chinese: Grandpa, I'll come to accompany you when I finish my studies in China . Then the old man stroked the child's head "
input.input_urls
Optional
array(URL)
Upload 0-2 images. Leave empty to generate video from text only.

Please provide the URL of the uploaded file; Accepted types: image/jpeg, image/png, image/webp; Max size: 10.0MB
Example:

["https://static.aiquickdraw.com/tools/example/1766556007862_Y451Ehaf.png"]
input.aspect_ratio
Required
string
Select the frame dimensions. Default is 1:1.

Available options:

1:1
-
1:1
21:9
-
21:9
4:3
-
4:3
3:4
-
3:4
16:9
-
16:9
9:16
-
9:16
Example:

"1:1"
input.resolution
Optional
string
Standard (480p) / High (720p)

Available options:

480p
-
480p
720p
-
720p
Example:

"720p"
input.duration
Required
string
4s / 8s / 12s

Available options:

4
-
4s
8
-
8s
12
-
12s
Example:

"8"
input.fixed_lens
Optional
boolean
Enable to keep the camera view static and stable. Disable for dynamic camera movement.

Boolean value (true/false)
input.generate_audio
Optional
boolean
Enable to create sound effects for the video (Additional cost applies).

Boolean value (true/false)
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
    "model": "bytedance/seedance-1.5-pro",
    "callBackUrl": "https://your-domain.com/api/callback",
    "input": {
        "prompt": "In a Chinese-English communication scenario,  a 70-year-old  old man said kindly to the child:  Good boy, study hard where you are in China !  The child happily replied in Chinese:  Grandpa, I'll come to accompany you when I finish my studies in China . Then the old man stroked the child's head ",
        "input_urls": [
            "https://static.aiquickdraw.com/tools/example/1766556007862_Y451Ehaf.png"
        ],
        "aspect_ratio": "1:1",
        "resolution": "720p",
        "duration": "8"
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
        "model": "bytedance/seedance-1.5-pro",
        "param": "{\"callBackUrl\":\"https://your-domain.com/api/callback\",\"model\":\"bytedance/seedance-1.5-pro\",\"input\":{\"prompt\":\"In a Chinese-English communication scenario,  a 70-year-old  old man said kindly to the child:  Good boy, study hard where you are in China !  The child happily replied in Chinese:  Grandpa, I'll come to accompany you when I finish my studies in China . Then the old man stroked the child's head \",\"input_urls\":[\"https://static.aiquickdraw.com/tools/example/1766556007862_Y451Ehaf.png\"],\"aspect_ratio\":\"1:1\",\"resolution\":\"720p\",\"duration\":\"8\"}}",
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
        "model": "bytedance/seedance-1.5-pro",
        "param": "{\"callBackUrl\":\"https://your-domain.com/api/callback\",\"model\":\"bytedance/seedance-1.5-pro\",\"input\":{\"prompt\":\"In a Chinese-English communication scenario,  a 70-year-old  old man said kindly to the child:  Good boy, study hard where you are in China !  The child happily replied in Chinese:  Grandpa, I'll come to accompany you when I finish my studies in China . Then the old man stroked the child's head \",\"input_urls\":[\"https://static.aiquickdraw.com/tools/example/1766556007862_Y451Ehaf.png\"],\"aspect_ratio\":\"1:1\",\"resolution\":\"720p\",\"duration\":\"8\"}}",
        "state": "fail",
        "taskId": "bd3a37c523149e4adf45a3ddb5faf1a8",
        "resultJson": null,
    },
    "msg": "Playground task failed."
}