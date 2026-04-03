import json
import boto3
import os
import logging
import base64

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")
polly = boto3.client("polly")
s3 = boto3.client("s3")

TABLE_NAME = os.environ.get("TABLE_NAME")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")
S3_BUCKET = os.environ.get("S3_BUCKET")

table = dynamodb.Table(TABLE_NAME)


def handler(event, context):
    try:
        logger.info(f"EVENT: {event}")

        http_method = event.get("requestContext", {}).get("http", {}).get("method")
        raw_path = event.get("rawPath", "")
        path_params = event.get("pathParameters") or {}

        # =========================
        # 1. POST /metrics
        # =========================
        if http_method == "POST" and raw_path == "/metrics":
            body = json.loads(event.get("body") or "{}")
            value = int(body.get("value", 0))

            response = table.get_item(Key={"id": "main"})
            threshold = int(response["Item"]["threshold"])

            alert_sent = False

            if value > threshold:
                message = f"""
                🚨 ALERT NOTIFICATION 🚨

                Value: {value}
                Threshold: {threshold}
                """
                sns.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Subject="🚨 ALERT",
                    Message=message
                )
                alert_sent = True

            return {
                "statusCode": 200,
                "body": json.dumps({"alert_sent": alert_sent})
            }

        # =========================
        # 2. POST /notes/{id}/analyze
        # =========================
        if http_method == "POST" and raw_path.startswith("/notes/"):
            note_id = path_params.get("id")

            body = json.loads(event.get("body") or "{}")
            text = body.get("text", "")

            try:
                # 🔥 AI-аналіз (імітація)
                sentiment = "positive" if "good" in text.lower() else "negative"

                # запис у DynamoDB
                table.put_item(
                    Item={
                        "id": f"note-{note_id}",
                        "text": text,
                        "sentiment": sentiment
                    }
                )

                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "note_id": note_id,
                        "sentiment": sentiment
                    })
                }

            except Exception as e:
                logger.error(str(e))
                return {
                    "statusCode": 500,
                    "body": str(e)
                }

        # =========================
        # 3. GET /alerts/{id}/audio
        # =========================
        if http_method == "GET" and raw_path.startswith("/alerts/"):
            alert_id = path_params.get("id")

            text = f"Warning! Threshold exceeded. Alert number {alert_id}."

            response = polly.synthesize_speech(
                Text=text,
                OutputFormat="mp3",
                VoiceId="Joanna"
            )

            audio_stream = response["AudioStream"].read()
            file_key = f"alerts/{alert_id}.mp3"

            s3.put_object(
                Bucket=S3_BUCKET,
                Key=file_key,
                Body=audio_stream,
                ContentType="audio/mpeg"
            )

            url = s3.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": S3_BUCKET, "Key": file_key},
                ExpiresIn=3600
            )

            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "audio/mpeg"
                },
                "isBase64Encoded": True,
                "body": base64.b64encode(audio_stream).decode("utf-8")
            }

        # =========================
        return {
            "statusCode": 405,
            "body": json.dumps({"message": "Method Not Allowed"})
        }

    except Exception as e:
        logger.error(str(e))
        return {
            "statusCode": 500,
            "body": str(e)
        }