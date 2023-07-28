import importlib
import inspect
import os
import shutil
from contextlib import contextmanager
from time import sleep

import click
import shortuuid
from python_on_whales import DockerException, ClientNotFoundError, DockerClient, docker
from mako.template import Template


INIT_TYPE_CHOICES = ['all', 'rpc', 'event', 'http', 'timer', 'demo']
MIDDLEWARE_CHOICES = ['rabbitmq', 'metrics']
TEST_TYPE_CHOICES = ['unit']


def check_docker():
    """
    Check if docker and docker compose are installed and running.
    """
    try:
        docker.ps()
    except ClientNotFoundError:
        click.echo('Please install docker first', err=True)
        raise
    except DockerException:
        click.echo('Please start docker correctly', err=True)
        raise

    if not docker.compose.is_installed():
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


def template_to_file(
        template_file: str, dest: str, output_encoding: str, **kw
) -> None:
    template = Template(filename=template_file)
    try:
        output = template.render_unicode(**kw).encode(output_encoding)
    except Exception as e:
        click.echo('Template rendering failed.', err=True)
        raise
    else:
        with open(dest, "wb") as f:
            f.write(output)


def start_rabbitmq():
    docker_compose_file_dir = os.path.join(get_directory('chassis-agent'), 'rabbitmq')
    for file_ in os.listdir(docker_compose_file_dir):
        compose_file_path = os.path.join(docker_compose_file_dir, file_)
        with status(f'Starting rabbitmq'):
            temp_docker = DockerClient(compose_files=[compose_file_path])
            temp_docker.compose.up(detach=True)


def start_statsd_agent():
    with status(f'Starting statsd agent'):
        metric_configs_dir = os.path.join(get_directory('chassis-agent'), 'metric-configs')
        statsd_config_file_path = os.path.join(metric_configs_dir, 'statsd_config.js')
        returned_string = docker.run(image='statsd/statsd:latest', name='statsd-agent', hostname='statsd-agent',
                                     detach=True, restart='always', interactive=True, tty=True,
                                     publish=[(8125, 8125, 'udp'), (8126, 8126)], pull='missing',
                                     volumes=[(statsd_config_file_path, '/usr/src/app/config.js', 'rw')],
                                     networks=['metric_servers'])
        click.echo('\nContainer ID: ' + str(returned_string) + '\n')


def start_statsd_exporter():
    with status(f'Starting statsd exporter'):
        statsd_mapping_file_path = os.path.join('.', 'statsd_mapping.yml')
        returned_string = docker.run(image='prom/statsd-exporter:latest', name='statsd-exporter', pull='missing',
                                     detach=True, restart='always', tty=True, hostname='statsd-exporter',
                                     publish=[(9125, 9125, 'udp'), (9102, 9102)], interactive=True,
                                     command=['--statsd.mapping-config=/tmp/statsd_mapping.yml'],
                                     volumes=[(statsd_mapping_file_path, '/tmp/statsd_mapping.yml', 'rw')],
                                     networks=['metric_servers'])
        click.echo('\nContainer ID: ' + str(returned_string) + '\n')


def start_prometheus():
    with status(f'Starting prometheus'):
        prometheus_conf_dir = os.path.join(get_directory('chassis-agent'), 'metric-configs')
        prometheus_conf_file_path = os.path.join(prometheus_conf_dir, 'prometheus_conf/prometheus.yml')
        returned_string = docker.run(image='prom/prometheus:latest', name='prometheus', hostname='prometheus',
                                     detach=True, restart='always', tty=True, interactive=True,
                                     publish=[(9193, 9090)], pull='missing',
                                     volumes=[(prometheus_conf_file_path, '/etc/prometheus/prometheus.yml', 'rw')],
                                     networks=['metric_servers'])
        click.echo('\nContainer ID: ' + str(returned_string) + '\n')


def start_grafana():
    with status(f'Starting grafana'):
        grafana_conf_dir = os.path.join(get_directory('chassis-agent'), 'metric-configs')
        grafana_provisioning_path = os.path.join(grafana_conf_dir, 'grafana_conf/provisioning')
        grafana_config_path = os.path.join(grafana_conf_dir, 'grafana_conf/config/grafana.ini')
        grafana_dashboard_path = os.path.join('.', 'grafana_dashboards')
        returned_string = docker.run(image='grafana/grafana:latest', name='grafana', hostname='grafana',
                                     detach=True, restart='always', tty=True, interactive=True,
                                     publish=[(3100, 3000)], pull='missing',
                                     volumes=[(grafana_provisioning_path, '/etc/grafana/provisioning', 'rw'),
                                              (grafana_config_path, '/etc/grafana/grafana.ini', 'rw'),
                                              (grafana_dashboard_path, '/var/lib/grafana/dashboards', 'rw')],
                                     networks=['metric_servers'])
        click.echo('\nContainer ID: ' + str(returned_string) + '\n')


def start_network(network_name):
    with status(f'Starting network {network_name}'):
        docker.network.create(network_name, driver='bridge')


def stop_network(network_name):
    with status(f'Stopping network {network_name}'):
        docker.network.remove(network_name)


def start_metric_servers():
    start_network('metric_servers')
    sleep(0.5)
    start_prometheus()
    sleep(0.5)
    start_statsd_exporter()
    sleep(0.5)
    start_statsd_agent()
    sleep(0.5)
    start_grafana()


def stop_rabbitmq():
    docker_compose_file_dir = os.path.join(get_directory('chassis-agent'), 'rabbitmq')
    for file_ in os.listdir(docker_compose_file_dir):
        compose_file_path = os.path.join(docker_compose_file_dir, file_)
        with status(f'Stopping rabbitmq'):
            temp_docker = DockerClient(compose_files=[compose_file_path])
            temp_docker.compose.down()


def stop_statsd_agent():
    with status(f'Stopping statsd agent'):
        docker.remove('statsd-agent', force=True)
        click.echo('\nContainer is removed.' + '\n')


def stop_statsd_exporter():
    with status(f'Stopping statsd exporter'):
        docker.remove('statsd-exporter', force=True)
        click.echo('\nContainer is removed.' + '\n')


def stop_prometheus():
    with status(f'Stopping prometheus'):
        docker.remove('prometheus', force=True)
        click.echo('\nContainer is removed.' + '\n')


def stop_grafana():
    with status(f'Stopping grafana'):
        docker.remove('grafana', force=True)
        click.echo('\nContainer is removed.' + '\n')


def stop_metric_servers():
    stop_statsd_agent()
    sleep(0.5)
    stop_statsd_exporter()
    sleep(0.5)
    stop_prometheus()
    sleep(0.5)
    stop_grafana()
    sleep(0.5)
    stop_network('metric_servers')


middleware_starting_dict = {
    'rabbitmq': start_rabbitmq,
    'metrics': start_metric_servers,
}

middleware_stopping_dict = {
    'rabbitmq': stop_rabbitmq,
    'metrics': stop_metric_servers,
}


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
              type=click.Choice(INIT_TYPE_CHOICES, case_sensitive=False),
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
              type=click.Choice(MIDDLEWARE_CHOICES, case_sensitive=False),
              help='The middleware name')
def start(middleware):
    """
    Start a middleware that the nameko service depends on.
    """
    check_docker()
    middleware_starting_dict.get(middleware)()


@cli.command()
@click.option('-m', '--middleware',
              required=True,
              type=click.Choice(MIDDLEWARE_CHOICES, case_sensitive=False),
              help='The middleware name')
def stop(middleware):
    """
    Stop a middleware that the nameko service depends on.
    """
    check_docker()
    middleware_stopping_dict.get(middleware)()


@cli.command()
@click.option('-e', '--existed_dir', 'directory',
              required=True,
              help='The existed directory name of the nameko service')
@click.option('-t', '--type', '_type',
              default='unit',
              show_default=True,
              type=click.Choice(TEST_TYPE_CHOICES, case_sensitive=False),
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


@cli.command()
@click.option('-m', '--module',
              required=True,
              help='The module name where the nameko service exists')
@click.option('-c', '--class', 'class_name_str',
              required=True,
              help='The class name of the nameko service')
def metric_config_gen(module, class_name_str):
    """
    Generate metric config for nameko services.
    """
    import sys
    from statsd.client.timer import Timer
    sys.path.append(os.getcwd()) 

    # Extract information of statsd config from the class of nameko service
    dest_dir = module.split('.')[0]
    file_name = module.split('.')[-1]
    _module = __import__(module)

    config_list = []
    for class_name in class_name_str.split(','):
        members = inspect.getmembers(getattr(getattr(_module, file_name), class_name), predicate=inspect.isfunction)
        for member_tuple in members:
            name, _obj = member_tuple
            unwrap = inspect.getclosurevars(_obj)
            if unwrap.nonlocals.get('self') and isinstance(unwrap.nonlocals['self'], Timer):
                statsd_prefix = unwrap.nonlocals['self'].client._prefix
                stat_name = unwrap.nonlocals['self'].stat
                config_list.append({
                    'statsd_prefix': statsd_prefix,
                    'stat_name': stat_name,
                    'class_name': class_name
                })

    # Generate one file of statsd config yaml for statsd exporter
    with status(f'Creating statsd_mapping.yml'):
        metric_configs_dir = os.path.join(get_directory('chassis-agent'), 'metric-configs')
        template_file_path = os.path.join(metric_configs_dir, 'statsd_mapping.yml.mako')
        output_file = os.path.join('.', 'statsd_mapping.yml')
        template_to_file(template_file=template_file_path, dest=output_file, output_encoding='utf-8',
                         **{'config_list': config_list})

    # Generate files of json for grafana dashboard
    if not os.access('grafana_dashboards', os.F_OK):
        with status(f'Creating directory {os.path.abspath("grafana_dashboards")!r}'):
            os.makedirs('grafana_dashboards')

    with status(f'Creating files of Grafana.json into the directory of grafana_dashboards'):
        for class_name in class_name_str.split(','):
            grafana_list = []
            for config in config_list:
                if config['class_name'] == class_name:
                    grafana_list.append(config)
            grafana_configs_dir = os.path.join(get_directory('chassis-agent'), 'metric-configs')
            grafana_file_path = os.path.join(grafana_configs_dir, 'grafana.json.mako')
            output_file = os.path.join('grafana_dashboards', f'{class_name}_Grafana.json')
            template_to_file(template_file=grafana_file_path, dest=output_file, output_encoding='utf-8',
                             **{'service_name': class_name, 'uid': shortuuid.uuid(),
                                'grafana_list': grafana_list})


if __name__ == '__main__':
    cli()
