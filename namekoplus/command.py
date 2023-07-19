import os
import shutil
from contextlib import contextmanager

import click


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
    """Return the directory where nameko_plus setup templates are found.

    This method is used by the nameko_plus ``init`` commands.
    """
    import namekoplus

    package_dir = os.path.abspath(os.path.dirname(namekoplus.__file__))
    return os.path.join(package_dir, 'templates')


@click.group()
def cli():
    pass


@cli.command()
@click.option('-d', '--directory',
              required=True,
              help='The directory name of nameko services')
@click.option('-f', '--type', '_type',
              default='rpc',
              show_default=True,
              type=click.Choice(['rpc', 'event', 'http', 'timer'], case_sensitive=False),
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
def start():
    """
    Start a middleware, such as RabbitMQ.
    """
    click.echo('Initialized the database')


if __name__ == '__main__':
    cli()