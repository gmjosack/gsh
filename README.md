# gsh

### Description

GSH is a pluggable version of DSH (Distributed Shell) written in Python. Both
a module and a command-line tool for running a shell command over multiple
machines are included. GSH can be extended by adding new host loaders as well
as hooking into various stages of the runtime.

While I plan to keep the api stable for the command line, the module's interface
and plugin interfaces are still potentially evolving and I can't guarantee all
changes will be backwards compatible at this time.

### Installation

New versions will be updated to PyPI pretty regularly so it should be as easy
as:

```bash
pip install gsh
```

### Configuration

Many of the default configuration options can be overridden with a
configuration file. Configuration is currently specified as a YAML
document. The following is what the default configuration would
look like:

```yaml
forklimit: 64
print_machines: true
concurrent: true
timeout: null
plugin_dirs: [ ]
hooks: []
```

Configuration files are read from the following locations, being overridden
in the order they are read:

 * _/etc/gsh/gsh.yaml_
 * _~/.gsh/gsh.yaml_

### Group Files

One of the default host loaders (-g) allows you to specify group files by name.
Group files contain a newline delimited list of hosts with an option user@
specified. This loader will search for these files in the following locations

 * _~/.gsh/group_
 * _~/.dsh/group_
 * _/etc/gsh/group_
 * _/etc/dsh/group_

The first group file found will win. The loader will not continue searching
through all paths. An example group that might be accessed when a user
types the command __gsh -g test_hosts uptime__ would be:

_/etc/gsh/group/test_hosts_
```bash
test_host1.example.com
test_host2.example.com
# Users can be specified. Also comments are ignored.
roleaccount@test_host2.example.com
```

### Plugins

##### Loaders

##### Hooks

### Rationale

Over the last several years DSH has been invaluable to my career as a System's
Administrator, however it has a few shortcomings which have come up over time.
I've always wanted to extend DSH in various ways specific to my environment
and usually ended up with various wrapper scripts to load hosts from inventory
databases.

I specifically chose Python for this project as it is the language I use most
often and this allows me to use it as a module without shelling out. While
benchmarks have shown GSH to be slower, the overhead seems to be near
constant. Considering the extensibililty, and that most of the time spend is
waiting on network I/O, I consider this a fair tradeoff.

### Improvements

Besides the loaders and hooks mentioned in other sections, GSH provides a few
general benefits over DSH.

__Specifying a loader option (-m/-g/etc) without a command will list the hosts.__

Many times I'd like to just see which hosts are in a group. As I added new host
loaders for dynamically building host lists this became a more common desire.
With DSH if you failed to specify a command it would just SSH to your machines
and exit. GSH will print the list of machines that would be be used in the
absense of a command.


__The fork limit (-F) can be specified as a percentage.__

Often times you'll end up scripting rolling restarts of services over various
groups of hosts. You might end up specifying a fork limit of 24 forgetting one
of your smaller web pools is smaller than that causing them to all be
restarted at once, causing an outage. Your options previously were lowering
the limit to the lowest common denominator or writing annoying wrapper scripts.
GSH allows you to specify the fork limit as a percentage.
e.g. gsh -g mobileweb -F 20% "/etc/init.d/nginx restart"


__ps utput is cleaner / less forking madness.__

While this may seem like a silly thing to list as an improvement, it has
sufficiently improved my quality of life. In DSH you saw 3 forks for each
host that you were connected to. This made it annoying to find which process
you should be killing when it hung. It's also utilizing more processes for
no noticable benefit. An example of DSH output is as follows:

```
bash
 \_ dsh -Mcg test_hosts uptime
     \_ dsh -Mcg test_host1 uptime
     |   \_ dsh -Mcg test_host1 uptime
     |       \_ rsh test_host1 uptime
     \_ dsh -Mcg test_host2 uptime
         \_ dsh -Mcg test_host2 uptime
             \_ rsh test_host2 uptime

```

This is GSH output for comparison:

```
bash
 \_ python gsh -g test_hosts uptime
     \_ ssh test_host1 uptime
     \_ ssh test_host2 uptime
```

__Timeouts!__

Speaking of having to know which processes to kill when they've hung... GSH
provides a timeout option. While setting your SSH connection timeout is nice,
sometimes the command just hangs indefinitely and you want to get your shell
back. The -t option of gsh will timeout long running processes after the
specified allotment of time. Be careful with this though as it will kill you
command ungracefully (-9).

__Concurrency improvements.__

DSH had this weird issue where it couldn't do a fork limit of 1. It would
always have one more host than you has specified. This is a behavior I
did not replicate. A fork limit of 1 is now synonymous with serial execution
mode. In addition to this change I have instituted a default fork limit of 64.
DSH would gladly kill your machine by default by forking way too many
processes. This limit can be overridden on the command line or in your
personal or system configuration files, however no option exists to
eliminate this limit.


### F.A.Q.
__What the hell does GSH stand for?__

GSH stand's for Gary's Shell. Mostly just because I didn't know what to call
it and it's close to DSH. Plus who doesn't want a piece of software named
after themselves.

__How do you pronounce GSH?__

You can either pronounce each character individually or some of us at work
have taken to calling it "geesh." The G in geesh is pronounced like the G
in gum and not like a J.

