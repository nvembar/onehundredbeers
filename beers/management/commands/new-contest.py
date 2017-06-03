from django.core.management.base import BaseCommand, CommandError
from django.db.models import Model
from django.utils import timezone
from beers.models import Beer, Player, Contest_Checkin, Contest_Beer, Contest, Contest_Player
from beers.utils.loader import create_contest_from_csv
from dateutil.parser import parse
from django.conf import settings
import boto3
import os
import tempfile
import io
import json

class Command(BaseCommand):

    help = "Creates a new contest and loads its beer from a CSV"

    def add_arguments(self, parser):
        parser.add_argument('name', nargs=1, help='Contest Name')
        parser.add_argument('runner', nargs=1, help='Contest Runner')
        parser.add_argument('start_date', nargs=1, help='Contest Start Date')
        parser.add_argument('end_date', nargs=1, help='Contest End Date')
        parser.add_argument('bucket', nargs=1, help='S3 Bucket')
        parser.add_argument('file', nargs=1, help='S3 CSV Object')

    def handle(self, *args, **opts):
        if Contest.objects.filter(name=opts['name'][0]).count() > 0:
            raise ValueError("Contest {} already exists".format(opts['name'][0]))
        runner = None
        try:
            runner = Player.objects.get(user__username=opts['runner'][0])
        except Player.DoesNotExist:
            raise ValueError("No such user {}".format(opts['runner'][0]))
        start_date = parse(opts['start_date'][0])
        end_date = parse(opts['end_date'][0])

        sts = boto3.client('sts')
        role_response = sts.assume_role(RoleArn=settings.LOADER_ROLE_ARN,
                        RoleSessionName='LoadContest',)
        print(role_response)
        s3 = boto3.resource('s3',
            aws_access_key_id=role_response['Credentials']['AccessKeyId'],
            aws_secret_access_key=role_response['Credentials']['SecretAccessKey'],
            aws_session_token=role_response['Credentials']['SessionToken'],)
        with tempfile.TemporaryFile() as stream:
            s3_object = s3.Object(opts['bucket'][0], opts['file'][0])
            s3_object.download_fileobj(stream)
            stream.seek(0)
            text = io.TextIOWrapper(stream)
            create_contest_from_csv(name=opts['name'][0],
                start_date=start_date, end_date=end_date,
                runner=runner, stream=text,)
