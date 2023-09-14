#!/usr/bin/ruby

# Get the base directory
baseDir=File.expand_path('../..',__FILE__)

# Add bin directory to require search path
$LOAD_PATH.unshift "#{baseDir}/bin"

# Load libs
require 'date'
require 'yaml'
require 'fileutils'
require 'leadTime.rb'

# Load the experiment config
expConfig = YAML.load_file(ARGV[0])

# Get the experiment forecast time range parameters
expStart=DateTime.parse(expConfig['Experiment']['Begin']).to_time
expFreq=LeadTime.fcstToSeconds(expConfig['Experiment']['Cycle Frequency'])
expEnd=expStart + LeadTime.fcstToSeconds(expConfig['Experiment']['Length']) - expFreq

# Run each cycle 
t=expStart
while t <= expEnd

  puts "Running cycle: #{t.inspect}"

  # Run the assimilation if needed
  if t > expStart
    system("#{baseDir}/bin/runAssimilation.rb #{ARGV[0]} #{t.strftime("%Y-%m-%dT%H:%M:%SZ")}")
  end

  # Run the forecast
  system("#{baseDir}/bin/runForecast.rb #{ARGV[0]} #{t.strftime("%Y-%m-%dT%H:%M:%SZ")}")

  t = t + expFreq

end
