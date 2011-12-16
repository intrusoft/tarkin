#!/usr/bin/env sh

# Martin and Joe mind meld

for i in `euca-describe-instances | grep i- | awk '{print $2}'`; do euca-terminate-instances $i; done


