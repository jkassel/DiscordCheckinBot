import os
from aws_cdk import (
    Stack,
    aws_secretsmanager as secretsmanager,
    aws_apigatewayv2 as apigw,
    aws_apigatewayv2_integrations as integrations,
    aws_lambda as _lambda,
    aws_iam as iam,
    Duration,
    BundlingOptions,
    Fn,
    CfnOutput
)

from constructs import Construct


class DiscordCheckinBotStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, app_name: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Import API Gateway ID and Endpoint from Shared Stack
        api_gateway_id = Fn.import_value("ApiGatewayId")
        api_endpoint = Fn.import_value("ApiGatewayEndpoint")

        # Import the existing API Gateway
        http_api = apigw.HttpApi.from_http_api_attributes(
            self,
            f"{app_name}DiscordBotSharedApi",
            http_api_id=api_gateway_id,
            api_endpoint=api_endpoint,
        )

        checkin_discord_bot_secret = secretsmanager.Secret.from_secret_name_v2(
            self,
            "CheckinDiscordBotSecrets",
            secret_name=f"{app_name}/Prod/CheckinBot/DiscordSecrets",
        )

        checkin_google_maps_secret = secretsmanager.Secret.from_secret_name_v2(
            self,
            "CheckinGoogleMapsSecret",
            secret_name=f"{app_name}/Prod/CheckinBot/GoogleAPIKey",
        )

        checkin_bot_lambda_role = iam.Role(
            self,
            "CheckinBotLambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )

        checkin_discord_bot_secret.grant_read(checkin_bot_lambda_role)
        checkin_google_maps_secret.grant_read(checkin_bot_lambda_role)

        lambda_code_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../")
        )

        # Define the Lambda function with Bundling for dependencies
        checkin_bot_lambda = _lambda.Function(
            self,
            "CheckInBotLambda",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="checkin_bot_main.lambda_handler",
            code=_lambda.Code.from_asset(
                lambda_code_path + "/lambda",
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_11.bundling_image,
                    command=[
                        "bash",
                        "-c",
                        "pip install --cache-dir=/tmp/.pip-cache -r requirements.txt -t /asset-output && cp -r . /asset-output",
                    ],
                ),
            ),
            role=checkin_bot_lambda_role,
            environment={
                "DISCORD_BOT_SECRET_ARN": checkin_discord_bot_secret.secret_arn,
                "GOOGLE_MAPS_SECRET_ARN": checkin_google_maps_secret.secret_arn,
                "LOG_LEVEL": "DEBUG",
            },
            timeout=Duration.seconds(60),
        )

        http_integration = integrations.HttpLambdaIntegration(
            f"{app_name}CheckinBotIntegration",
            handler=checkin_bot_lambda,
            payload_format_version=apigw.PayloadFormatVersion.VERSION_2_0,
        )

        # Create the route explicitly
        apigw.HttpRoute(
            self,
            f"{app_name}CheckinBotRoute",
            http_api=http_api,
            route_key=apigw.HttpRouteKey.with_("/checkin-bot", apigw.HttpMethod.POST),
            integration=http_integration,
        )

        # Output the API Gateway URL for easy access
        CfnOutput(
            self,
            f"{app_name}CheckinBotApiEndpoint",
            value=http_api.api_endpoint + "/checkin-bot",
        )

