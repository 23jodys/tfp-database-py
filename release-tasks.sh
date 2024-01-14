#!/bin/bash

set -o pipefail
set -e
set -x

flask --app "tfp_widget:create_app('production')" db upgrade