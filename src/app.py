import json
import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")

TABLE_NAME = os.environ.get("TABLE_NAME")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")

table = dynamodb.Table(TABLE_NAME)

def handler(event, context):
    try:
        logger.info(f"EVENT: {event}")

        http_method = event["requestContext"]["httpMethod"]

        if http_method == "POST":
            body = json.loads(event.get("body") or "{}")
            value = int(body.get("value", 0))

            response = table.get_item(Key={"id": "main"})
            threshold = int(response["Item"]["threshold"])

            logger.info(f"Value: {value}, Threshold: {threshold}")

            alert_sent = False

            if value > threshold:
                message = f"""
                🚨 ALERT NOTIFICATION 🚨

                Hello!

                We detected that a monitored value has exceeded the allowed threshold.

                📊 Details:
                - Current value: {value}
                - Threshold: {threshold}

                Please take the necessary actions.

                Best regards,  
                Your Monitoring System
                """
                sns.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Subject="🚨 ALERT: Threshold Exceeded",
                    Message=message
                )
                alert_sent = True

            return {
                "statusCode": 200,
                "body": json.dumps({"alert_sent": alert_sent})
            }

        return {
            "statusCode": 405,
            "body": json.dumps({"message": "Method Not Allowed"})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": str(e)
        }