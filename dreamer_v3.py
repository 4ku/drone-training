from drone_aviary.envs import TakeoffAviary, LandingAviary
import warnings
import dreamerv3
from dreamerv3 import embodied
warnings.filterwarnings('ignore', '.*truncated to dtype int32.*')

# See configs.yaml for all options.
config = embodied.Config(dreamerv3.configs['defaults'])
config = config.update(dreamerv3.configs['small'])
config = config.update({
    'logdir': 'tensorboard/run1',
    'run.train_ratio': 64,
    'run.log_every': 30,  # Seconds
    'run.save_every': 300,  # Seconds
    'run.from_checkpoint': '',
    'batch_size': 16,
    'jax.prealloc': True,
    'encoder.mlp_keys': '$^',
    'decoder.mlp_keys': '$^',
    'encoder.cnn_keys': 'image',
    'decoder.cnn_keys': 'image',
    'replay_size': 150000,
    # 'jax.platform': 'cpu',
})
config = embodied.Flags(config).parse()

logdir = embodied.Path(config.logdir)
step = embodied.Counter()
logger = embodied.Logger(step, [
    embodied.logger.TerminalOutput(),
    embodied.logger.JSONLOutput(logdir, 'metrics.jsonl'),
    embodied.logger.TensorBoardOutput(logdir),
    # embodied.logger.WandBOutput(logdir.name, config),
    # embodied.logger.MLFlowOutput(logdir.name),
])

from embodied.envs import from_gym


# env = LandingAviary(gui=False, record=False)
env = TakeoffAviary(gui=False, record=False)
env = from_gym.FromGym(env, obs_key='image')  # Or obs_key='vector'.
env = dreamerv3.wrap_env(env, config)
env = embodied.BatchEnv([env], parallel=False)

agent = dreamerv3.Agent(env.obs_space, env.act_space, step, config)
replay = embodied.replay.Uniform(
    config.batch_length, config.replay_size, logdir / 'replay')
args = embodied.Config(
    **config.run, logdir=config.logdir,
    batch_steps=config.batch_size * config.batch_length)
embodied.run.train(agent, env, replay, logger, args)
# embodied.run.eval_only(agent, env, logger, args)


