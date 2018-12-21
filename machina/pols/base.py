# Copyright 2018 DeepX Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================


import gym
import numpy as np
import torch
import torch.nn as nn


class BasePol(nn.Module):
    def __init__(self, ob_space, ac_space, net, rnn=False, normalize_ac=True, data_parallel=False, parallel_dim=0):
        nn.Module.__init__(self)
        self.ob_space = ob_space
        self.ac_space = ac_space
        self.net = net

        self.rnn = rnn
        self.hs = None

        self.normalize_ac = normalize_ac
        self.data_parallel = data_parallel
        if data_parallel:
            self.dp_net = nn.DataParallel(self.net, dim=parallel_dim)
        self.dp_run = False

        self.discrete = isinstance(ac_space, gym.spaces.MultiDiscrete) or isinstance(ac_space, gym.spaces.Discrete)
        self.multi = isinstance(ac_space, gym.spaces.MultiDiscrete)

        if not self.discrete:
            self.pd_shape = ac_space.shape
        else:
            if isinstance(ac_space, gym.spaces.MultiDiscrete):
                nvec = ac_space.nvec
                assert any([nvec[0] == nv for nv in nvec])
                self.pd_shape = (len(nvec), nvec[0])
            elif isinstance(ac_space, gym.spaces.Discrete):
                self.pd_shape = (ac_space.n, )

    def convert_ac_for_real(self, x):
        if not self.discrete:
            lb, ub = self.ac_space.low, self.ac_space.high
            if self.normalize_ac:
                x = lb + (x + 1.) * 0.5 * (ub - lb)
                x = np.clip(x, lb, ub)
            else:
                x = np.clip(x, lb, ub)
        return x

    def reset(self):
        if self.rnn:
            self.hs = None

    def _check_obs_shape(self, obs):
        if self.rnn:
            additional_shape = 2
        else:
            additional_shape = 1
        if len(obs.shape) < additional_shape + len(self.ob_space.shape):
            for _ in range(additional_shape + len(self.ob_space.shape) - len(obs.shape)):
                obs = obs.unsqueeze(0)
        return obs
