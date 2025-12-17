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
