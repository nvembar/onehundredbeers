"""Command to create a new contest"""

import io
import tempfile
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.conf import settings
from beers.models import Contest, Player
from beers.utils.loader import create_contest_from_csv
from dateutil.parser import parse
import boto3


class Command(BaseCommand):
    """
    Command to create a new contest from a CSV stored in an S3 bucket.
    """

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
            raise CommandError(('Contest {} already '
                                + 'exists').format(opts['name'][0]))
        runner = None
        try:
            runner = Player.objects.get(user__username=opts['runner'][0])
        except Player.DoesNotExist:
            raise CommandError("No such user {}".format(opts['runner'][0]))
        start_date = timezone.make_aware(parse(opts['start_date'][0]))
        end_date = timezone.make_aware(parse(opts['end_date'][0]))

        sts = boto3.client('sts')
        role_response = sts.assume_role(RoleArn=settings.LOADER_ROLE_ARN,
                                        RoleSessionName='LoadContest',)
        access_key_id = role_response['Credentials']['AccessKeyId']
        secret_access_key = role_response['Credentials']['SecretAccessKey']
        session_token = role_response['Credentials']['SessionToken']
        s3 = boto3.resource('s3',
                            aws_access_key_id=access_key_id,
                            aws_secret_access_key=secret_access_key,
                            aws_session_token=session_token,)
        with tempfile.TemporaryFile() as stream:
            s3_object = s3.Object(opts['bucket'][0], opts['file'][0])
            s3_object.download_fileobj(stream)
            stream.seek(0)
            text = io.TextIOWrapper(stream)
            create_contest_from_csv(name=opts['name'][0],
                                    start_date=start_date,
                                    end_date=end_date,
                                    runner=runner,
                                    stream=text,)
