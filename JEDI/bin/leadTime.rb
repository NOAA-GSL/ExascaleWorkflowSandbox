class LeadTime

  ##################################
  #
  # fcstToSeconds
  #
  ##################################
  def self.fcstToSeconds(fcst)

    seconds=0
    if fcst =~ /[^\d]+(\d+)S/
      seconds += $1.to_i
    end
    if fcst =~ /[^\d]+(\d+)M/
      seconds += $1.to_i * 60
    end
    if fcst =~ /[^\d]+(\d+)H/
      seconds += $1.to_i * 3600
    end
    if fcst =~ /[^\d]+(\d+)D/
      seconds += $1.to_i * 3600 * 24
    end
    if fcst =~ /^M/   
      seconds = seconds * -1
    else
      seconds
    end

  end


  ##################################
  #
  # secondsToFcst
  #
  ##################################
  def self.secondsToFcst(s)

    seconds = s.to_i

    fcst = ""
    if seconds < 0 
      fcst = "M"
    else
      fcst = "P"
    end

    days = seconds / (3600 * 24)
    if days > 0
      fcst = fcst + "#{days}D"
    end

    fcst = fcst + "T" unless (seconds % (3600 * 24) == 0) && (seconds != 0)

    hours = (seconds - days * 3600 * 24) / 3600
    if hours > 0
      fcst = fcst + "#{hours}H"
    end

    minutes = (seconds - days * 3600 * 24 - hours * 3600) / 60
    if minutes > 0
      fcst = fcst + "#{minutes}M"
    end

    seconds = seconds - days * 3600 * 24 - hours * 3600 - minutes * 60
    if (days == 0 && hours == 0 && minutes == 0) || (seconds > 0)
      fcst = fcst + "#{seconds}S"
    end

    fcst

  end

end
