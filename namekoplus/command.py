import os
import shutil
from contextlib import contextmanager

import click
from python_on_whales import DockerException, ClientNotFoundError, DockerClient, docker as docker_testing


def check_docker():
    try:
        docker_testing.ps()
    except ClientNotFoundError:
        click.echo('Please install docker first', err=True)
        raise
    except DockerException:
        click.echo('Please start docker correctly', err=True)
        raise

    if not docker_testing.compose.is_installed():
        click.echo('Please install docker-compose first', err=True)
        raise


@contextmanager
def status(status_msg: str, newline: bool = False, quiet: bool = False):
    msg_suffix = ' ...' if not newline else ' ...\n'
    click.echo(status_msg + msg_suffix)
    try:
        yield
    except Exception as e:
        if not quiet:
            click.echo('  FAILED\n')
        raise
    else:
        if not quiet:
            click.echo('  Done\n')


def get_template_directory() -> str:
    """
    Return the directory where nameko_plus setup templates are found.
    """
    import namekoplus

    package_dir = os.path.abspath(os.path.dirname(namekoplus.__file__))
    return os.path.join(package_dir, 'templates')


def get_agent_directory() -> str:
    """
    Return the directory where nameko_plus setup agent are found.
    """
    import namekoplus

    package_dir = os.path.abspath(os.path.dirname(namekoplus.__file__))
    return os.path.join(package_dir, 'chassis-agent')


@click.group()
def cli():
    pass


@cli.command()
@click.option('-d', '--directory',
              required=True,
              help='The directory name of nameko services')
@click.option('-t', '--type', '_type',
              default='all',
              show_default=True,
              type=click.Choice(['all', 'rpc', 'event', 'http', 'timer', 'demo'], case_sensitive=False),
              help='The template type of nameko service')
def init(directory, _type):
    """
    Initialize a new service via templates.
    """
    if os.access(directory, os.F_OK) and os.listdir(directory):
        click.echo('Directory {} already exists and is not empty'.format(directory), err=True)
        return

    template_dir = os.path.join(get_template_directory(), _type)
    if not os.access(template_dir, os.F_OK):
        click.echo('No such template type {}'.format(_type), err=True)
        return

    # 创建目录
    if not os.access(directory, os.F_OK):
        with status(f'Creating directory {os.path.abspath(directory)!r}'):
            os.makedirs(directory)

    # 把 templates 放入新建的目录
    for file_ in os.listdir(template_dir):
        if file_ == '__pycache__':
            continue
        src_file_path = os.path.join(template_dir, file_)
        output_file = os.path.join(directory, file_)
        with status(f'Generating {os.path.abspath(output_file)}'):
            shutil.copy(src_file_path, output_file)


@cli.command()
@click.option('-m', '--middleware',
              required=True,
              type=click.Choice(['rabbitmq'], case_sensitive=False),
              help='The middleware name')
@click.option('-u', '--user',
              required=False,
              help='The user name of the middleware')
@click.option('-p', '--password',
              required=False,
              help='The password of the middleware')
def start(middleware, user, password):
    """
    Start a middleware that the nameko service depends on.
    """
    check_docker()

    if user and password:
        os.environ['RABBITMQ_DEFAULT_USER'] = user
        os.environ['RABBITMQ_DEFAULT_PASS'] = password

    docker_compose_file_dir = os.path.join(get_agent_directory(), middleware)
    for file_ in os.listdir(docker_compose_file_dir):
        compose_file_path = os.path.join(docker_compose_file_dir, file_)
        with status(f'Starting {middleware}'):
            docker = DockerClient(compose_files=[compose_file_path])
            docker.compose.up(detach=True)


@cli.command()
@click.option('-m', '--middleware',
              required=True,
              type=click.Choice(['rabbitmq'], case_sensitive=False),
              help='The middleware name')
def stop(middleware):
    """
    Stop a middleware that the nameko service depends on.
    """
    check_docker()

    docker_compose_file_dir = os.path.join(get_agent_directory(), middleware)
    for file_ in os.listdir(docker_compose_file_dir):
        compose_file_path = os.path.join(docker_compose_file_dir, file_)
        with status(f'Stopping {middleware}'):
            docker = DockerClient(compose_files=[compose_file_path])
            docker.compose.down()


if __name__ == '__main__':
    cli()