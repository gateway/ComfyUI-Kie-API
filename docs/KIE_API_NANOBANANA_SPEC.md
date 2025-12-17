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


KIE AI FILE UPLOAD Stream endpoint to use.. 

# File Stream Upload

## OpenAPI

````yaml file-upload-api/file-upload-api.json post /api/file-stream-upload
openapi: 3.0.0
info:
  title: File Upload API
  description: >-
    File Upload Service API Documentation - Supporting multiple file upload
    methods, uploaded files are temporary and automatically deleted after 3 days
  version: 1.0.0
  contact:
    name: Technical Support
    email: support@kie.ai
servers:
  - url: https://kieai.redpandaai.co
    description: API Server
security:
  - BearerAuth: []
paths:
  /api/file-stream-upload:
    post:
      summary: File Stream Upload
      operationId: upload-file-stream
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file:
                  type: string
                  format: binary
                  description: File to upload (binary data)
                uploadPath:
                  type: string
                  description: File upload path, without leading or trailing slashes
                  example: images/user-uploads
                fileName:
                  type: string
                  description: >-
                    File name (optional), including file extension. If not
                    provided, a random file name will be generated. If the same
                    file name is uploaded again, the old file will be
                    overwritten, but changes may not take effect immediately due
                    to caching
                  example: my-image.jpg
              required:
                - file
                - uploadPath
      responses:
        '200':
          $ref: '#/components/responses/SuccessResponse'
        '400':
          $ref: '#/components/responses/BadRequestError'
        '401':
          $ref: '#/components/responses/UnauthorizedError'
        '500':
          $ref: '#/components/responses/ServerError'
components:
  responses:
    SuccessResponse:
      description: File uploaded successfully
      content:
        application/json:
          schema:
            type: object
            properties:
              success:
                type: boolean
                description: Whether the request was successful
              code:
                type: integer
                enum:
                  - 200
                  - 400
                  - 401
                  - 405
                  - 500
                description: >-
                  Response Status Code


                  | Code | Description |

                  |------|-------------|

                  | 200 | Success - Request has been processed successfully |

                  | 400 | Bad Request - Request parameters are incorrect or
                  missing required parameters |

                  | 401 | Unauthorized - Authentication credentials are missing
                  or invalid |

                  | 405 | Method Not Allowed - Request method is not supported |

                  | 500 | Server Error - An unexpected error occurred while
                  processing the request |
              msg:
                type: string
                description: Response message
                example: File uploaded successfully
              data:
                $ref: '#/components/schemas/FileUploadResult'
            required:
              - success
              - code
              - msg
              - data
          example:
            success: true
            code: 200
            msg: File uploaded successfully
            data:
              fileName: uploaded-image.png
              filePath: images/user-uploads/uploaded-image.png
              downloadUrl: >-
                https://tempfile.redpandaai.co/xxx/images/user-uploads/uploaded-image.png
              fileSize: 154832
              mimeType: image/png
              uploadedAt: '2025-01-01T12:00:00.000Z'
    BadRequestError:
      description: Request parameter error
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ApiResponse'
          examples:
            missing_parameter:
              summary: Missing required parameter
              value:
                success: false
                code: 400
                msg: 'Missing required parameter: uploadPath'
            invalid_format:
              summary: Format error
              value:
                success: false
                code: 400
                msg: 'Base64 decoding failed: Invalid Base64 format'
    UnauthorizedError:
      description: Unauthorized access
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ApiResponse'
          example:
            success: false
            code: 401
            msg: 'Authentication failed: Invalid API Key'
    ServerError:
      description: Internal server error
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ApiResponse'
          example:
            success: false
            code: 500
            msg: Internal server error
  schemas:
    FileUploadResult:
      type: object
      properties:
        fileName:
          type: string
          description: File name
          example: uploaded-image.png
        filePath:
          type: string
          description: Complete file path in storage
          example: images/user-uploads/uploaded-image.png
        downloadUrl:
          type: string
          format: uri
          description: File download URL
          example: >-
            https://tempfile.redpandaai.co/xxx/images/user-uploads/uploaded-image.png
        fileSize:
          type: integer
          description: File size in bytes
          example: 154832
        mimeType:
          type: string
          description: File MIME type
          example: image/png
        uploadedAt:
          type: string
          format: date-time
          description: Upload timestamp
          example: '2025-01-01T12:00:00.000Z'
      required:
        - fileName
        - filePath
        - downloadUrl
        - fileSize
        - mimeType
        - uploadedAt
    ApiResponse:
      type: object
      properties:
        success:
          type: boolean
          description: Whether the request was successful
        code:
          $ref: '#/components/schemas/StatusCode'
        msg:
          type: string
          description: Response message
          example: File uploaded successfully
      required:
        - success
        - code
        - msg
    StatusCode:
      type: integer
      enum:
        - 200
        - 400
        - 401
        - 405
        - 500
      description: >-
        Response Status Code


        | Code | Description |

        |------|-------------|

        | 200 | Success - Request has been processed successfully |

        | 400 | Bad Request - Request parameters are incorrect or missing
        required parameters |

        | 401 | Unauthorized - Authentication credentials are missing or invalid
        |

        | 405 | Method Not Allowed - Request method is not supported |

        | 500 | Server Error - An unexpected error occurred while processing the
        request |
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: API Key
      description: >-
        All APIs require authentication via Bearer Token.


        Get API Key:

        1. Visit [API Key Management Page](https://kie.ai/api-key) to get your
        API Key


        Usage:

        Add to request header:

        Authorization: Bearer YOUR_API_KEY

````

---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.kie.ai/llms.txt.
