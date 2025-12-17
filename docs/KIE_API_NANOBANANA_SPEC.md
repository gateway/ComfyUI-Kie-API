## Credits (official)
GET https://api.kie.ai/api/v1/chat/credit
Header: Authorization: Bearer YOUR_API_KEY

Response:
{
  "code": 200,
  "msg": "success",
  "data": 100
}
- data = remaining credits (integer)


# KIE Nano Banana Pro API (Pinned)
- API key loaded from config/kie_key.txt
- Create task: POST /api/v1/jobs/createTask
- Poll task: GET /api/v1/jobs/recordInfo?taskId=
- Credits: GET https://api.kie.ai/api/v1/chat/credit with header `Authorization: Bearer <token>`; expects JSON `{ "code": 200, "msg": "success", "data": <remaining_credits_int> }` and treat non-200 code as error.

Nano Banan Pro API endpoint info and docs do not use anything other than whats below

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

"nano-banana-pro"
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

Max length: 10000 characters
Example:

"Comic poster: cool banana hero in shades leaps from sci-fi pad. Six panels: 1) 4K mountain landscape, 2) banana holds page of long multilingual text with auto translation, 3) Gemini 3 hologram for search/knowledge/reasoning, 4) camera UI sliders for angle focus color, 5) frame trio 1:1-9:16, 6) consistent banana poses. Footer shows Google icons. Tagline: Nano Banana Pro now on Kie AI."
input.image_input
Optional
array(URL)
Input images to transform or use as reference (supports up to 8 images)

File URL after upload, not file content; Accepted types: image/jpeg, image/png, image/webp; Max size: 30.0MB
input.aspect_ratio
Optional
string
Aspect ratio of the generated image

Available options:

1:1
-
1:1
2:3
-
2:3
3:2
-
3:2
3:4
-
3:4
4:3
-
4:3
4:5
-
4:5
5:4
-
5:4
9:16
-
9:16
16:9
-
16:9
21:9
-
21:9
auto
-
Auto
Example:

"1:1"
input.resolution
Optional
string
Resolution of the generated image

Available options:

1K
-
1K
2K
-
2K
4K
-
4K
Example:

"1K"
input.output_format
Optional
string
Format of the output image

Available options:

png
-
PNG
jpg
-
JPG
Example:

"png"
Request Example

cURL

JavaScript

Python
curl -X POST "https://api.kie.ai/api/v1/jobs/createTask" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "nano-banana-pro",
    "callBackUrl": "https://your-domain.com/api/callback",
    "input": {
      "prompt": "Comic poster: cool banana hero in shades leaps from sci-fi pad. Six panels: 1) 4K mountain landscape, 2) banana holds page of long multilingual text with auto translation, 3) Gemini 3 hologram for search/knowledge/reasoning, 4) camera UI sliders for angle focus color, 5) frame trio 1:1-9:16, 6) consistent banana poses. Footer shows Google icons. Tagline: Nano Banana Pro now on Kie AI.",
      "aspect_ratio": "1:1",
      "resolution": "1K",
      "output_format": "png"
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
        "model": "nano-banana-pro",
        "param": "{\"callBackUrl\":\"https://your-domain.com/api/callback\",\"model\":\"nano-banana-pro\",\"input\":{\"prompt\":\"Comic poster: cool banana hero in shades leaps from sci-fi pad. Six panels: 1) 4K mountain landscape, 2) banana holds page of long multilingual text with auto translation, 3) Gemini 3 hologram for search/knowledge/reasoning, 4) camera UI sliders for angle focus color, 5) frame trio 1:1-9:16, 6) consistent banana poses. Footer shows Google icons. Tagline: Nano Banana Pro now on Kie AI.\",\"image_input\":[],\"aspect_ratio\":\"1:1\",\"resolution\":\"1K\",\"output_format\":\"png\"}}",
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
        "model": "nano-banana-pro",
        "param": "{\"callBackUrl\":\"https://your-domain.com/api/callback\",\"model\":\"nano-banana-pro\",\"input\":{\"prompt\":\"Comic poster: cool banana hero in shades leaps from sci-fi pad. Six panels: 1) 4K mountain landscape, 2) banana holds page of long multilingual text with auto translation, 3) Gemini 3 hologram for search/knowledge/reasoning, 4) camera UI sliders for angle focus color, 5) frame trio 1:1-9:16, 6) consistent banana poses. Footer shows Google icons. Tagline: Nano Banana Pro now on Kie AI.\",\"image_input\":[],\"aspect_ratio\":\"1:1\",\"resolution\":\"1K\",\"output_format\":\"png\"}}",
        "remainedCredits": 2510430,
        "state": "fail",
        "taskId": "bd3a37c523149e4adf45a3ddb5faf1a8",
        "updateTime": 1755597097000
    },
    "msg": "Playground task failed."
}
.
