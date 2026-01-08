Kling 26 Motion I2V 

inputs
- Ref Image (Single Image)
- Motion video (Single mp4)

These files are uploaded to Kie AI similar to how we upload the images in kling26_i2v.py how its done in their.

KIE API Documents:

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

"kling-2.6/motion-control"
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
A text description of the desired output. Maximum length is 2500 characters.

Max length: 2500 characters
Example:

"The cartoon character is dancing."
input.input_urls
Required
array(URL)
An array containing a single image URL. The photo must clearly show the subject's head, shoulders, and torso.

Please provide the URL of the uploaded file; Accepted types: image/jpeg, image/png, image/webp; Max size: 10.0MB
Example:

["https://static.aiquickdraw.com/tools/example/1767694885407_pObJoMcy.png"]
input.video_urls
Required
array(URL)
An array containing a single video URL. The duration must be between 3 to 30 seconds, and the video must clearly show the subject's head, shoulders, and torso.The minimum width and height for videos must be 720 pixels, and only jpeg/jpg/png image formats are supported.

Please provide the URL of the uploaded file; Accepted types: video/mp4, video/quicktime, video/x-matroska; Max size: 100.0MB
Example:

["https://static.aiquickdraw.com/tools/example/1767525918769_QyvTNib2.mp4"]
input.character_orientation
Required
string
Generate the orientation of the characters in the video. 'image': same orientation as the person in the picture (max 10s video). 'video': consistent with the orientation of the characters in the video (max 30s video).

Available options:

image
-
Image
video
-
Video
Example:

"video"
input.mode
Required
string
Output resolution mode. Use 'std' for 720p or 'pro' for 1080p.

Available options:

720p
-
720p
1080p
-
1080p
Example:

"720p"
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
    "model": "kling-2.6/motion-control",
    "callBackUrl": "https://your-domain.com/api/callback",
    "input": {
        "prompt": "The cartoon character is dancing.",
        "input_urls": [
            "https://static.aiquickdraw.com/tools/example/1767694885407_pObJoMcy.png"
        ],
        "video_urls": [
            "https://static.aiquickdraw.com/tools/example/1767525918769_QyvTNib2.mp4"
        ],
        "character_orientation": "video",
        "mode": "720p"
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
        "model": "kling-2.6/motion-control",
        "param": "{\"callBackUrl\":\"https://your-domain.com/api/callback\",\"model\":\"kling-2.6/motion-control\",\"input\":{\"prompt\":\"The cartoon character is dancing.\",\"input_urls\":[\"https://static.aiquickdraw.com/tools/example/1767694885407_pObJoMcy.png\"],\"video_urls\":[\"https://static.aiquickdraw.com/tools/example/1767525918769_QyvTNib2.mp4\"],\"character_orientation\":\"video\",\"mode\":\"720p\"}}",
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
        "model": "kling-2.6/motion-control",
        "param": "{\"callBackUrl\":\"https://your-domain.com/api/callback\",\"model\":\"kling-2.6/motion-control\",\"input\":{\"prompt\":\"The cartoon character is dancing.\",\"input_urls\":[\"https://static.aiquickdraw.com/tools/example/1767694885407_pObJoMcy.png\"],\"video_urls\":[\"https://static.aiquickdraw.com/tools/example/1767525918769_QyvTNib2.mp4\"],\"character_orientation\":\"video\",\"mode\":\"720p\"}}",
        "state": "fail",
        "taskId": "bd3a37c523149e4adf45a3ddb5faf1a8",
        "resultJson": null,
    },
    "msg": "Playground task failed."
}
Important Notes
The callback content structure is identical to the Query Task API response
The param field contains the complete Create Task request parameters, not just the input section
If callBackUrl is not provided, no callback notifications will be sent