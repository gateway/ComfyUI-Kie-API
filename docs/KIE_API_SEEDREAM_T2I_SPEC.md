SEEDREAM 4.5 T2I API INFORMATION

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

"seedream/4.5-text-to-image"
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
A text description of the image you want to generate

Max length: 3000 characters
Example:

"A full-process cafe design tool for entrepreneurs and designers. It covers core needs including store layout, functional zoning, decoration style, equipment selection, and customer group adaptation, supporting integrated planning of \"commercial attributes + aesthetic design.\" Suitable as a promotional image for a cafe design SaaS product, with a 16:9 aspect ratio."
input.aspect_ratio
Required
string
Width-height ratio of the image, determining its visual form.

Available options:

1:1
-
1:1
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
2:3
-
2:3
3:2
-
3:2
21:9
-
21:9
Example:

"1:1"
input.quality
Required
string
Basic outputs 2K images, while High outputs 4K images.

Available options:

basic
-
Basic
high
-
High
Example:

"basic"
Request Example

cURL

JavaScript

Python
curl -X POST "https://api.kie.ai/api/v1/jobs/createTask" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "seedream/4.5-text-to-image",
    "callBackUrl": "https://your-domain.com/api/callback",
    "input": {
      "prompt": "A full-process cafe design tool for entrepreneurs and designers. It covers core needs including store layout, functional zoning, decoration style, equipment selection, and customer group adaptation, supporting integrated planning of \"commercial attributes + aesthetic design.\" Suitable as a promotional image for a cafe design SaaS product, with a 16:9 aspect ratio.",
      "aspect_ratio": "1:1",
      "quality": "basic"
    }
}'
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
        "model": "seedream/4.5-text-to-image",
        "param": "{\"callBackUrl\":\"https://your-domain.com/api/callback\",\"model\":\"seedream/4.5-text-to-image\",\"input\":{\"prompt\":\"A full-process cafe design tool for entrepreneurs and designers. It covers core needs including store layout, functional zoning, decoration style, equipment selection, and customer group adaptation, supporting integrated planning of \\"commercial attributes + aesthetic design.\\" Suitable as a promotional image for a cafe design SaaS product, with a 16:9 aspect ratio.\",\"aspect_ratio\":\"1:1\",\"quality\":\"basic\"}}",
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
        "model": "seedream/4.5-text-to-image",
        "param": "{\"callBackUrl\":\"https://your-domain.com/api/callback\",\"model\":\"seedream/4.5-text-to-image\",\"input\":{\"prompt\":\"A full-process cafe design tool for entrepreneurs and designers. It covers core needs including store layout, functional zoning, decoration style, equipment selection, and customer group adaptation, supporting integrated planning of \\"commercial attributes + aesthetic design.\\" Suitable as a promotional image for a cafe design SaaS product, with a 16:9 aspect ratio.\",\"aspect_ratio\":\"1:1\",\"quality\":\"basic\"}}",
        "remainedCredits": 2510430,
        "state": "fail",
        "taskId": "bd3a37c523149e4adf45a3ddb5faf1a8",
        "updateTime": 1755597097000
    },
    "msg": "Playground task failed."
}