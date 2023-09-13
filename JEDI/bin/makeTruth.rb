#!/usr/bin/ruby

# Get the base directory
baseDir=File.expand_path('../..',__FILE__)

# Add bin directory to require search path
$LOAD_PATH.unshift "#{baseDir}/bin"

# Load libs
require 'yaml'
require 'fileutils'
require 'date'
require 'leadTime.rb'

# Load the experiment config
expConfig = YAML.load_file(ARGV[0])

# Load the base truth config template
truthConfig = YAML.load_file("#{baseDir}/yaml/truth.yaml")

# Create experiment truth output directory
expDir = "#{baseDir}/experiments/#{expConfig['Experiment']['Name']}"
FileUtils.rm_rf("#{expDir}/truth")
FileUtils.mkdir_p("#{expDir}/truth")

# Set configuration truth initial conditions
truthConfig["initial"]["filename"] = "#{baseDir}/input_data/truth.an.#{expConfig['Experiment']['Begin']}.l95"
truthConfig["initial"]["date"] = expConfig['Experiment']['Begin']

# Set configuration truth length
truthConfig["forecast_length"] = LeadTime.secondsToFcst(LeadTime.fcstToSeconds(expConfig['Experiment']['Length']) + LeadTime.fcstToSeconds(expConfig['Forecast']['Length']))

# Set configuration truth output
truthConfig["output"]["datadir"] = "#{expDir}/truth"
truthConfig["output"]["frequency"] = expConfig['Forecast']['Frequency']
truthConfig["output"]["date"] = expConfig['Experiment']['Begin']

# Write out updated truth config
FileUtils.mkdir_p("#{expDir}/yaml")
File.open("#{expDir}/yaml/truth.yaml", "w") { |f| YAML.dump(truthConfig, f) }

# Save the experiment config
File.open("#{expDir}/yaml/#{expConfig['Experiment']['Name']}.yaml", "w") { |f| YAML.dump(expConfig, f) }

# Run the truth forecast
system("#{expConfig['JEDI Path']}/bin/l95_forecast.x #{expDir}/yaml/truth.yaml > #{expDir}/truth/makeTruth.stdout")

if $?.exitstatus != 0
  raise "makeTruth failed!  See #{expDir}/truth/makeTruth.stdout"
end

exit $?.exitstatus
