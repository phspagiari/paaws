# -*- coding: utf-8 -*-
from paaws.config.arn import arn_constructor

def get_sns_topic_arn(platform, region):
    arn_infra = arn_constructor(service="sns", region=region, name="sns-infra")
    topics = [arn_infra]
    if platform in ('billing', 'messaging', 'ticketing', 'verification', 'listing'):
                topics.append(arn_constructor(service="sns", region=region, name="sns-sistemas"))
    elif platform == 'cloud':
                topics.append(arn_constructor(service="sns", region=region, name="sns-cloud"))
    elif platform == 'security':
                topics.append(arn_constructor(service="sns", region=region, name="sns-security"))
    elif platform == 'learning':
                topics.append(arn_constructor(service="sns", region=region, name="sns-learning"))

    return topics
