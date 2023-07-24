import os
import shutil
from contextlib import contextmanager

import click
from python_on_whales import DockerException, ClientNotFoundError, DockerClient, docker as docker_testing


def check_docker():
    """
    Check if docker and docker compose are installed and running.
    """
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
    """
    Show status message and yield.
    """
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


def get_directory(dir_name: str) -> str:
    """
    Return the directory path of the given nameko-plus directory name.
    """
    import namekoplus

    package_dir = os.path.abspath(os.path.dirname(namekoplus.__file__))
    return os.path.join(package_dir, dir_name)


def copy_files(src_dir, dest_dir):
    for file_ in os.listdir(src_dir):
        if file_ == '__pycache__':
            continue

        src_file_path = os.path.join(src_dir, file_)
        output_file = os.path.join(dest_dir, file_)
        with status(f'Generating {os.path.abspath(output_file)}'):
            shutil.copy(src_file_path, output_file)


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

    template_dir = os.path.join(get_directory('templates'), _type)
    if not os.access(template_dir, os.F_OK):
        click.echo('No such template type {}'.format(_type), err=True)
        return

    if not os.access(directory, os.F_OK):
        with status(f'Creating directory {os.path.abspath(directory)!r}'):
            os.makedirs(directory)

    copy_files(template_dir, directory)


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

    docker_compose_file_dir = os.path.join(get_directory('chassis-agent'), middleware)
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

    docker_compose_file_dir = os.path.join(get_directory('chassis-agent'), middleware)
    for file_ in os.listdir(docker_compose_file_dir):
        compose_file_path = os.path.join(docker_compose_file_dir, file_)
        with status(f'Stopping {middleware}'):
            docker = DockerClient(compose_files=[compose_file_path])
            docker.compose.down()


@cli.command()
@click.option('-e', '--existed_dir', 'directory',
              required=True,
              help='The existed directory name of the nameko service')
@click.option('-t', '--type', '_type',
              default='unit',
              show_default=True,
              type=click.Choice(['unit'], case_sensitive=False),
              help='The test type of the nameko service')
def test_gen(directory, _type):
    """
    Generate test files for nameko services.
    """
    if not os.access(directory, os.F_OK) or not os.listdir(directory):
        click.echo('Directory {} dose not exist or is empty'.format(directory), err=True)
        return

    tests_dir = os.path.join(get_directory('tests'), _type)
    if not os.access(tests_dir, os.F_OK):
        click.echo('No such test type {}'.format(_type), err=True)
        return

    copy_files(tests_dir, directory)


if __name__ == '__main__':
    cli()